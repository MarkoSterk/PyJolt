"""Controller class for endpoint groups"""


from typing import (Callable, TYPE_CHECKING, Optional, Type)

from pydantic import BaseModel
from ..media_types import MediaType
from ..http_statuses import HttpStatus

if TYPE_CHECKING:
    from ..pyjolt import PyJolt

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

        for name in dir(owner_cls):
            method = getattr(owner_cls, name)
            if not callable(method):
                continue
            endpoint_handler = getattr(method, "_handler", {})
            if endpoint_handler:
                http_method: str = endpoint_handler.get("http_method") # type: ignore
                endpoints[http_method][endpoint_handler["path"]] = {"method": method,
                                                                    **endpoint_handler}
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


class Descriptor:

    def __init__(self, status: HttpStatus = HttpStatus.BAD_REQUEST,
                 description: Optional[str] = None,
                 media_type: MediaType = MediaType.APPLICATION_JSON,
                 body: Optional[Type[BaseModel]] = None):
        self._status = status
        self._description = description
        self._body = body
        self._media_type = media_type

    @property
    def status(self) -> HttpStatus:
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
