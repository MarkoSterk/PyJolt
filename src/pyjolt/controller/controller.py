"""Controller class for endpoint groups"""


from typing import (Callable, TYPE_CHECKING, Optional, Type, TypeVar)

from pydantic import BaseModel
from ..media_types import MediaType
from ..http_statuses import HttpStatus
from ..utilities import run_sync_or_async

if TYPE_CHECKING:
    from ..pyjolt import PyJolt
    from ..response import Response
    from ..request import Request

T = TypeVar("T", bound="Controller")

def path(url_path: str = "/", open_api_spec: bool = True) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, "_controller_path", url_path)
        setattr(cls, "_include_open_api_spec", open_api_spec)
        return cls

    return decorator

class Controller:

    def __init__(self, app: "PyJolt", path: str = "/", open_api_spec: bool = True):
        self._app = app
        self._path = path
        self._before_request_methods: list[Callable] = []
        self._after_request_methods: list[Callable] = []
        self._controller_decorator_methods: list[Callable] = []
        self._endpoints_map: dict[str, dict[str, str|Callable]] = []
        self._open_api_spec = open_api_spec
        self.get_before_request_methods()
        self.get_after_request_methods()
        # print("Before req methods: ", self._before_request_methods)
        # print("After req methods: ", self._after_request_methods)

    def get_endpoint_methods(self) -> dict[str, dict[str, str|Callable]]:
        """Returns a dictionery with all endpoint methods"""
        owner_cls: "type[Controller]" = self.__class__ or None
        endpoints: dict[str, dict] = {
            "GET": {},
            "POST": {},
            "PUT": {},
            "PATCH": {},
            "DELETE": {}
        }
        if owner_cls is None:
            return endpoints

        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            endpoint_handler = getattr(method, "_handler", None)
            if endpoint_handler:
                http_method: str = endpoint_handler.get("http_method") # type: ignore
                endpoints[http_method][endpoint_handler["path"]] = {"method": method,
                                                                    "base_path": self._path,
                                                                    **endpoint_handler}
        self._endpoints_map = endpoints
        return endpoints
    
    def get_before_request_methods(self):
        owner_cls: "type[Controller]" = self.__class__ or None
        if owner_cls is None:
            return

        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            handler = getattr(method, "_before_request", None)
            if handler:
              self._before_request_methods.append(method)  
    
    def get_after_request_methods(self):
        owner_cls: "type[Controller]" = self.__class__ or None
        if owner_cls is None:
            return

        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            handler = getattr(method, "_after_request", None)
            if handler:
              self._after_request_methods.append(method)

    @property
    def endpoints_map(self) -> dict[str, dict[str, str|Callable]]:
        """Returns map of all endpoints"""
        return self._endpoints_map

    @property
    def path(self) -> str:
        """Path variable of the class"""
        return self._path
    
    @property
    def open_api_spec(self) -> bool:
        """If it is included in the open api specs"""
        return self._open_api_spec

    @property
    def app(self) -> "PyJolt":
        """App object"""
        return self._app


class Descriptor:

    def __init__(self, status: int|HttpStatus = HttpStatus.BAD_REQUEST,
                 description: Optional[str] = None,
                 media_type: MediaType = MediaType.APPLICATION_JSON,
                 body: Optional[Type[BaseModel]] = None):
        if isinstance(status, HttpStatus):
            status = status.value
        self._status = status
        self._description = description
        self._body = body
        self._media_type = media_type

    @property
    def status(self) -> HttpStatus|int:
        return self._status

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def body(self) -> Optional[Type[BaseModel]]:
        return self._body

    @property
    def media_type(self) -> MediaType:
        return self._media_type
