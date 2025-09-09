"""Controller class for endpoint groups"""

import inspect
import types
from typing import Callable, Optional, TYPE_CHECKING, ParamSpec, Type, TypeVar, cast
from functools import wraps

from .utilities import run_sync_or_async
from .exceptions import MethodNotControllerMethod

if TYPE_CHECKING:
    from .pyjolt import PyJolt
    from .response import Response

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
                endpoints[endpoint_handler["path"]] = {
                    "http_method": endpoint_handler["http_method"],
                    "method": method
                }
        self._endpoints_map = endpoints
        return endpoints

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

def path(path: str = "") -> Callable[[Type[T]], Type[T]]:
    def deco(cls) -> "Controller":
        setattr(cls, "_controller_path", path)
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
                    m(args[0] if args else None)

            if self._before_request_methods:
                for m in self._before_request_methods:
                    await run_sync_or_async(m, self, *args, **kwargs)
            response: "Response" = await run_sync_or_async(func, self, *args, **kwargs)
            if self._after_request_methods:
                for m in self._after_request_methods:
                    await run_sync_or_async(m, self, response, *args, **kwargs)

            return response
        wrapper._handler = {"http_method": "GET", "path": path} 
        return wrapper
    return decorator
