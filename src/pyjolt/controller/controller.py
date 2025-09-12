"""Controller class for endpoint groups"""

import inspect
from typing import (Any, Callable, TYPE_CHECKING,
                    ParamSpec, Type, TypeVar, get_origin, 
                    get_args, Annotated, Mapping, 
                    get_type_hints, Optional)
from functools import wraps
from enum import StrEnum
from pydantic import BaseModel, ValidationError

from ..utilities import run_sync_or_async
from ..exceptions import MethodNotControllerMethod, UnexpectedDecorator
from ..response import Response

if TYPE_CHECKING:
    from ..pyjolt import PyJolt
    from ..response import Request

class Controller:

    def __init__(self, app: "PyJolt", path: str = ""):
        self._app = app
        self._path = path
        self._before_request_methods: list[Callable] = []
        self._after_request_methods: list[Callable] = []
        self._controller_decorator_methods: list[Callable] = []
        self._endpoints_map: dict[str, dict[str, str|Callable]] = []
    
    def get_endpoint_methods(self) -> dict[str, dict[str, str|Callable]]:
        """Returns a dictionery with all endpoint methods"""
        owner_cls: "Controller" = self.__class__ or None
        endpoints: dict[str, Callable] = {}
        if owner_cls is None:
            return endpoints
        
        for name in dir(owner_cls):
            method = getattr(owner_cls, name)
            if not callable(method):
                continue
            endpoint_handler = getattr(method, "_handler", False)
            if endpoint_handler:
                endpoints[endpoint_handler["path"]] = {"method": method, **endpoint_handler}
        self._endpoints_map = endpoints
        return endpoints
    
    async def run_endpoint_method(self, method_name, *args, **kwargs) -> "Response":
        """Runs controller endpoint method"""
        

    @property
    def endpoints_map(self) -> dict[str, dict[str, str|Callable]]:
        """Returns map of all endpoints"""
        return self._endpoints_map   
    
    @property
    def path(self) -> str:
        """Path variable of the class"""
        return self._path
    
    @property
    def app(self) -> "PyJolt":
        """App object"""
        return self._app

T = TypeVar("T", bound=type)
P = ParamSpec("P")
R = TypeVar("R")

def path(url_path: str = "") -> Callable[[Type[T]], Type[T]]:
    def deco(cls) -> "Controller":
        setattr(cls, "_controller_path", url_path)
        return cls 
    return deco

def _get_handler_dict(obj: Any) -> dict[str, Any]:
    """Return or create the _handler dict on an object."""
    d = getattr(obj, "_handler", None)
    if not isinstance(d, dict):
        d = {}
        setattr(obj, "_handler", d)
    return d

def _unwrap_annotated(tp: Any) -> Any:
    """If Annotated[T, ...], return T; else the original."""
    if get_origin(tp) is Annotated:
        args = get_args(tp)
        return args[0] if args else tp
    return tp

def _is_subclass(x: Any, base: Type) -> bool:
    try:
        return inspect.isclass(x) and issubclass(x, base)
    except Exception:
        return False

def _is_pydantic_model(tp: Any) -> bool:
    return _is_subclass(tp, BaseModel)

def _build_model(model_cls: Type[BaseModel], data: Any) -> BaseModel:
    return model_cls.model_validate(data)  # type: ignore[attr-defined]

def _content_type_matches(incoming: str, expected: "MediaType") -> bool:
    """
    Accept parameters (e.g., '; charset=utf-8') and handle +json suffixes.
    """
    inc = (incoming or "").lower()
    exp = expected.value.lower()
    base = inc.split(";")[0].strip()

    if exp == MediaType.application_json.value:
        # RFC 6839: */*+json is valid too
        return base == "application/json" or base.endswith("+json")
    if exp == MediaType.application_problem_json.value:
        # RFC 7807; accept application/problem+json and */*+json
        return base in ("application/problem+json", "application/json") or base.endswith("+json")
    if exp == MediaType.multipart_form_data.value:
        return base == "multipart/form-data"
    if exp == MediaType.application_x_www_form_urlencoded.value:
        return base == "application/x-www-form-urlencoded"
    return base == exp

async def _read_payload_for_consumes(req: "Request", mt: "MediaType") -> Mapping[str, Any]:
    """
    Map declared MediaType → Request loader.
    Returns mapping suitable for building Pydantic models.
    """
    if mt in (MediaType.application_json, MediaType.application_problem_json):
        return (await req.json()) or {}
    if mt == MediaType.application_x_www_form_urlencoded:
        return await req.form()
    if mt == MediaType.multipart_form_data:
        return await req.form_and_files()
    #extend with additional types if needed.
    return {}

def _extract_response_type(func) -> Optional[Type[Any]]:
    """
    If the function is annotated as -> Response[T], return T; else None.
    """
    hints = get_type_hints(func, include_extras=True)
    ret = hints.get("return")
    if ret is None:
        return None
    if get_origin(ret) is Response:
        args = get_args(ret)
        if args:
            t = args[0]
            if get_origin(t) is Annotated:  # peel Annotated[T, ...]
                t = get_args(t)[0]
            return t
    return None

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

class MediaType(StrEnum):
    application_x_www_form_urlencoded = "application/x-www-form-urlencoded"
    multipart_form_data = "multipart/form-data"
    application_json = "application/json"
    application_problem_json = "application/problem+json"
    application_xml = "application/xml"
    text_xml = "text/xml"
    text_plain = "text/plain"
    text_html = "text/html"
    application_octet_stream = "application/octet-stream"
    image_png = "image/png"
    image_jpeg = "image/jpeg"
    image_gif = "image/gif"
    application_pdf = "application/pdf"
    application_x_ndjson = "application/x-ndjson"
    application_csv = "application/csv"
    text_csv = "text/csv"
    application_yaml = "application/yaml"
    text_yaml = "text/yaml"
    application_graphql = "application/graphql"  

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
                if ann in (dict, t.Dict, t.Mapping, dict[str, t.Any]):
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
