"""Controller class for endpoint groups"""


from typing import (Callable, TYPE_CHECKING)

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


