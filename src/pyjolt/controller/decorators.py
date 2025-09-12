"""
Controller decorators
"""
from typing import Callable, Optional, TypeVar, ParamSpec, Dict, Mapping, Any, Type
from functools import wraps
import inspect
from pydantic import ValidationError

from .controller import Controller
from .utilities import (_extract_response_type, get_type_hints, _unwrap_annotated,
                        _is_pydantic_model, _content_type_matches, 
                        _read_payload_for_consumes, _build_model)
from ..response import Response
from ..request import Request
from ..utilities import run_sync_or_async
from ..exceptions import MethodNotControllerMethod, UnexpectedDecorator
from ..media_types import MediaType


T = TypeVar("T", bound=type)
P = ParamSpec("P")
R = TypeVar("R")

def path(url_path: str = "") -> Callable[[Type[T]], Type[T]]:
    def deco(cls) -> "Controller":
        setattr(cls, "_controller_path", url_path)
        return cls 
    return deco

def get(path: str):
    """GET http handler decorator."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> "Response":
            if not isinstance(self, Controller):
                raise MethodNotControllerMethod(
                    f"Method {func.__name__} is not part of a valid controller class"
                )
            if self._controller_decorator_methods:
                for m in self._controller_decorator_methods:
                    await run_sync_or_async(m, self, *args, **kwargs)
            if self._before_request_methods:
                for m in self._before_request_methods:
                    await run_sync_or_async(m, self, *args, **kwargs)
            response: "Response" = await run_sync_or_async(func, self, *args, **kwargs)
            if self._after_request_methods:
                for m in self._after_request_methods:
                    await run_sync_or_async(m, self, response, *args, **kwargs)
            return response

        prev = getattr(func, "_handler", {}) or {}
        merged = dict(prev)
        merged.update({"http_method": "GET", "path": path})
        if merged.get("consumes", False):
            raise UnexpectedDecorator("Unexpected endpoint decorator. GET method endpoints can't consume request bodies.")
        wrapper._handler = merged
        return wrapper
    return decorator

def post(path: str):
    """POST http handler decorator."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> "Response":
            if not isinstance(self, Controller):
                raise MethodNotControllerMethod(
                    f"Method {func.__name__} is not part of a valid controller class"
                )
            req: "Request" = args[0]
            if req.response.expected_body_type is None:
                expected = _extract_response_type(func)
                req.response._set_expected_body_type(expected)
            if self._controller_decorator_methods:
                for m in self._controller_decorator_methods:
                    await run_sync_or_async(m, self, *args, **kwargs)
            if self._before_request_methods:
                for m in self._before_request_methods:
                    await run_sync_or_async(m, self, *args, **kwargs)
            response: "Response" = await run_sync_or_async(func, self, *args, **kwargs)
            if self._after_request_methods:
                for m in self._after_request_methods:
                    await run_sync_or_async(m, self, response, *args, **kwargs)
            return response

        prev = getattr(func, "_handler", {}) or {}
        merged = dict(prev)
        merged.update({"http_method": "POST", "path": path})
        wrapper._handler = merged
        return wrapper
    return decorator

def consumes(media_type: MediaType):
    """Decorator indicating what media type the endpoint consumes."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)

        try:
            hints = get_type_hints(func, include_extras=True)
        except Exception:
            hints = getattr(func, "__annotations__", {}) or {}

        consumed_type: Optional[Any] = None
        for name, param in list(sig.parameters.items())[2:]:  # skip self, req
            ann = hints.get(name, param.annotation)
            ann = _unwrap_annotated(ann)
            if _is_pydantic_model(ann):
                consumed_type = ann 

        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> "Response":
            # Request is auto-injected as the first arg after self
            if not args:
                raise RuntimeError("Request must be auto-injected as the first argument after self.")
            req = args[0]

            # Enforce Content-Type against declared consumes
            incoming_ct = req.headers.get("content-type", "")
            if not _content_type_matches(incoming_ct, media_type):
                return req.response.json(
                    {
                        "detail": "Unsupported Media Type",
                        "expected": media_type.value,
                        "received": incoming_ct or None,
                    }
                ).status(415)

            # Read payload once according to declared media type
            payload = await _read_payload_for_consumes(req, media_type)

            # Build missing typed params from payload.
            # Parameters: [0]=self, [1]=req, others start at index 2
            for name, param in list(sig.parameters.items())[2:]:
                if name in kwargs:
                    continue

                ann = hints.get(name, param.annotation)

                # If a parameter is a Pydantic model, validate from payload
                if _is_pydantic_model(ann):
                    try:
                        kwargs[name] = _build_model(ann, payload)
                    except ValidationError as ve:
                        return req.response.json(
                            {
                                "detail": "Validation error",
                                "errors": ve.errors() if hasattr(ve, "errors") else [],
                            },
                            status=422,
                        )
                    continue

                # Optionally inject raw dict mappings if the user wants that
                if ann in (dict, Dict, Mapping, dict[str, Any]):
                    kwargs[name] = payload
                    continue

                # Convenience injections by common names (optional)
                if name == "query_params":
                    kwargs[name] = req.query_params
                elif name == "route_params":
                    kwargs[name] = req.route_parameters
                elif name == "files":
                    kwargs[name] = await req.files()

            # Call original endpoint
            return await run_sync_or_async(func, self, *args, **kwargs)

        # Preserve/merge handler metadata on the wrapper
        prev = getattr(func, "_handler", {}) or {}
        merged = dict(prev)
        merged.update({"consumes": media_type, "consumes_type": consumed_type})
        wrapper._handler = merged
        return wrapper
    return decorator

def produces(*media_types: MediaType):
    """Decorator indicating what media types the endpoint produces."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        expected_body = _extract_response_type(func)

        @wraps(func)
        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> "Response":
            # Request is auto-injected as first arg after self
            if not args:
                raise RuntimeError("Request must be auto-injected as the first argument after self.")
            req = args[0]
            req.response._set_expected_body_type(expected_body)
            return await run_sync_or_async(func, self, *args, **kwargs)

        # Preserve/merge handler metadata (produces list)
        prev = getattr(func, "_handler", {}) or {}
        merged = dict(prev)
        merged.update({"produces": list(media_types)})
        wrapper._handler = merged
        return wrapper
    return decorator
