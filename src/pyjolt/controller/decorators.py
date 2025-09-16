"""
Controller decorators
"""

from typing import (
    Awaitable,
    Callable,
    Concatenate,
    Optional,
    Protocol,
    TypeVar,
    ParamSpec,
    Any,
    cast,
    overload,
)
from functools import wraps
import inspect
from loguru import logger

from .controller import Controller, Descriptor
from .utilities import (
    _extract_response_type,
    get_type_hints,
    _unwrap_annotated,
    _is_pydantic_model,
    _content_type_matches,
    _read_payload_for_consumes,
    _build_model,
)
from ..response import Response
from ..request import Request
from ..utilities import run_sync_or_async
from ..exceptions import MethodNotControllerMethod, UnexpectedDecorator
from ..media_types import MediaType
from ..http_methods import HttpMethod
from ..http_statuses import HttpStatus

P = ParamSpec("P")
R = TypeVar("R")
SelfT = TypeVar("SelfT", bound="Controller")


AsyncMeth = Callable[Concatenate[SelfT, P], Awaitable["Response"]]
SyncMeth  = Callable[Concatenate[SelfT, P], "Response"]

class _EndpointDecorator(Protocol[SelfT, P]): # type: ignore
    @overload
    def __call__(self, func: AsyncMeth) -> AsyncMeth: ...
    @overload
    def __call__(self, func: SyncMeth)  -> AsyncMeth: ...

# -------------------------
# GET
# -------------------------

def get(url_path: str, open_api_spec: bool = True,  tags: Optional[list[str]] = None) -> _EndpointDecorator["Controller", P]:
    """GET http handler decorator."""
    def decorator(func: Callable[..., object]) -> AsyncMeth:
        @wraps(func)
        async def wrapper(self: "Controller", *args: P.args, **kwargs: P.kwargs) -> "Response":
            if not isinstance(self, Controller):
                raise MethodNotControllerMethod(
                    f"Method {func.__name__} is not part of a valid controller class"
                )
            # pre-hooks
            for m in getattr(self, "_controller_decorator_methods", []) or []:
                await run_sync_or_async(m, self, *args, **kwargs)
            for m in getattr(self, "_before_request_methods", []) or []:
                await run_sync_or_async(m, self, *args, **kwargs)

            # call the original (sync or async)
            response: "Response" = await run_sync_or_async(func, self, *args, **kwargs)
            # post-hooks
            for m in getattr(self, "_after_request_methods", []) or []:
                await run_sync_or_async(m, self, response, *args, **kwargs)
            return response

        merged = {
            **(getattr(func, "_handler", {}) or {}),
            "http_method": HttpMethod.GET.value,
            "path": url_path,
            "open_api_spec": open_api_spec,
            "tags": tags if tags is not None else []
        }
        if merged.get("consumes", False):
            raise UnexpectedDecorator("GET endpoints can't consume request bodies.")
        # pylint: disable=protected-access
        wrapper._handler = merged  # type: ignore[attr-defined]
        return wrapper

    return cast(_EndpointDecorator["Controller", P], decorator)

# -------------------------
# POST, PUT, PATCH, DELETE
# -------------------------

#pylint: disable-next=C0301
def endpoint_decorator_factory(http_method: HttpMethod) -> Callable[[str, bool, Optional[list[str]]], _EndpointDecorator["Controller", P]]:
    def endpoint_decorator(url_path: str, open_api_spec: bool = True, tags: Optional[list[str]] = None) -> _EndpointDecorator["Controller", P]:
        """http handler decorator."""
        def decorator(func: Callable[..., object]) -> AsyncMeth:
            @wraps(func)
            async def wrapper(self: "Controller", *args: P.args, **kwargs: P.kwargs) -> "Response":
                if not isinstance(self, Controller):
                    raise MethodNotControllerMethod(
                        f"Method {func.__name__} is not part of a valid controller class"
                    )

                # Optionally infer/record expected response type for endpoint
                req: "Request" = args[0]  # type: ignore[index]
                if req.response.expected_body_type is None:
                    expected = _extract_response_type(func)
                    req.response._set_expected_body_type(expected)  # pylint: disable=protected-access

                # pre-hooks
                for m in getattr(self, "_controller_decorator_methods", []) or []:
                    await run_sync_or_async(m, self, *args, **kwargs)
                for m in getattr(self, "_before_request_methods", []) or []:
                    await run_sync_or_async(m, self, *args, **kwargs)

                # call the original (sync or async)
                response: "Response" = await run_sync_or_async(func, self, *args, **kwargs)

                # post-hooks
                for m in getattr(self, "_after_request_methods", []) or []:
                    await run_sync_or_async(m, self, response, *args, **kwargs)
                return response

            merged = {
                **(getattr(func, "_handler", {}) or {}),
                "http_method": http_method.value,
                "path": url_path,
                "open_api_spec": open_api_spec,
                "tags": tags if tags is not None else [],
            }
            # pylint: disable=protected-access
            wrapper._handler = merged  # type: ignore[attr-defined]
            return wrapper

        return cast(_EndpointDecorator["Controller", P], decorator)
    return endpoint_decorator

post = endpoint_decorator_factory(HttpMethod.POST)
put = endpoint_decorator_factory(HttpMethod.PUT)
patch = endpoint_decorator_factory(HttpMethod.PATCH)
delete = endpoint_decorator_factory(HttpMethod.DELETE)

def consumes(media_type: MediaType) -> _EndpointDecorator["Controller", P]:
    """Decorator indicating what media type the endpoint consumes."""

    def decorator(func: Callable[P, R]) -> AsyncMeth:
        sig = inspect.signature(func)

        try:
            hints = get_type_hints(func, include_extras=True)
        #pylint: disable-next=W0718
        except Exception:
            hints = getattr(func, "__annotations__", {}) or {}

        consumed_type: Optional[Any] = None
        for name, param in list(sig.parameters.items())[2:]:
            ann = hints.get(name, param.annotation)
            ann = _unwrap_annotated(ann)
            if _is_pydantic_model(ann):
                consumed_type = ann

        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> "Response":
            # Request is auto-injected as the first arg after self
            if not args:
                raise RuntimeError(
                    "Request must be auto-injected as the first argument after self."
                )
            req: "Request" = args[0] # type: ignore

            incoming_ct = req.headers.get("content-type", "")
            if not _content_type_matches(incoming_ct, media_type):
                return req.response.json(
                    {
                        "detail": "Unsupported Media Type",
                        "expected": media_type.value,
                        "received": incoming_ct or None,
                    }
                ).status(415)

            payload = await _read_payload_for_consumes(req, media_type)
            # Parameters: [0]=self, [1]=req, others start at index 2
            for name, param in list(sig.parameters.items())[2:]:
                if name in kwargs:
                    continue

                ann = hints.get(name, param.annotation)
                if _is_pydantic_model(ann):
                    kwargs[name] = _build_model(ann, payload)

            return await run_sync_or_async(func, self, *args, **kwargs)

        prev = getattr(func, "_handler", {}) or {}
        merged = dict(prev)
        merged.update({"consumes": media_type, "consumes_type": consumed_type})
        #pylint: disable-next=W0212
        wrapper._handler = merged # type: ignore
        return wrapper

    return decorator


def produces(media_type: MediaType, status_code: HttpStatus = HttpStatus.OK) -> _EndpointDecorator["Controller", P]:
    """Decorator indicating what media types the endpoint produces and what the default status code is"""

    def decorator(func: Callable[P, R]) -> AsyncMeth:
        expected_body = _extract_response_type(func)

        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> "Response":
            # Request is auto-injected as first arg after self
            if not args:
                raise RuntimeError(
                    "Request must be auto-injected as the first argument after self."
                )
            req: "Request" = args[0] # type: ignore
            #pylint: disable-next=W0212
            req.response._set_expected_body_type(expected_body)
            res: Response = await run_sync_or_async(func, self, *args, **kwargs)
            if res.headers.get("content-type", None) != media_type.value:
                logger.warning(f"Returned media type of method {func.__name__} does not match indicated produces type of {media_type.value}. Type will be set automatically. Consider changing indicated type.")
            res.set_header("content-type", media_type.value)
            return res

        # Preserve/merge handler metadata (produces list)
        prev = getattr(func, "_handler", {}) or {}
        merged = dict(prev)
        merged.update({"produces": media_type, "default_status_code": status_code})
        #pylint: disable-next=W0212
        wrapper._handler = merged # type: ignore
        return wrapper

    return decorator

def open_api_docs(*args: Descriptor):
    """Adds descriptions for error responses to OpenAPI documentation"""
    def decorator(func: AsyncMeth) -> AsyncMeth:
        prev = getattr(func, "_handler", {}) or {}
        merged = dict(prev)
        merged.update({"error_responses": list(args)})
        #pylint: disable-next=W0212
        func._handler = merged
        return func
    return decorator
