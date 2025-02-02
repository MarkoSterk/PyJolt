"""
Class blueprint
used for grouping related endpoints into a coherent group
"""
#pylint: disable=W0212
import sys
from typing import Callable
from functools import wraps

from marshmallow import Schema, ValidationError
from ..request import Request
from ..response import Response
from ..router import Router
from ..utilities import run_sync_or_async
from ..exceptions import (MissingRouterInstance, InvalidRouteHandler,
                          InvalidWebsocketHandler, MissingRequestData,
                          SchemaValidationError)

REQUEST_ARGS_ERROR_MSG: str = ("Injected argument 'req' of route handler is not an instance "
                        "of the Request class. If you used additional decorators "
                        "or middleware handlers make sure the order of arguments "
                        "was not changed. The Request and Response arguments "
                        "must always come first.")

RESPONSE_ARGS_ERROR_MSG: str = ()

def input_data(schema: Schema, many: bool = False,
              location: str = "json") -> Callable:
    """
    input decorator injects the received and validated data from json, form, multipart...
    locations into the route handler.
    Data is validated according to provided schema.
    """
    allowed_location: list[str] = ["json", "form", "files", "form_and_files", "query"]
    if location not in allowed_location:
        raise ValueError(f"Input data location must be one of: {allowed_location}")
    def decorator(handler) -> Callable:
        @wraps(handler)
        async def wrapper(*args, **kwargs):
            # Add `session` as the last positional argument
            req: Request = args[0]
            if not isinstance(req, Request):
                raise ValueError(REQUEST_ARGS_ERROR_MSG)
            data = await req.get_data(location)
            if data is None:
                raise MissingRequestData(f"Missing {location} request data.")
            try:
                kwargs[f"{location}_data"] = schema(many=many).load(data)
            except ValidationError as err:
                # pylint: disable-next=W0707
                raise SchemaValidationError(err.messages)
            return await run_sync_or_async(handler, *args, **kwargs)
        route_data: dict = getattr(wrapper, "is_route_handler", {})
        wrapper.is_route_handler = {
            **route_data,
            "openapi_request_schema": schema,
            "openapi_request_location": location
        }
        return wrapper
    return decorator

def output_data(schema: Schema,
              many: bool = False,
              status_code: int = 200,
              status_desc: str = "OK",
              field: str = None) -> Callable:
    """
    output decorator handels data serialization. Automatically serializes the data
    in the specified "field" of the route handler return dictionary. Default field name
    is the DEFAULT_RESPONSE_DATA_FIELD of the application (defaults to "data"). Sets the status_code (default 200)
    """
    def decorator(handler) -> Callable:
        @wraps(handler)
        async def wrapper(*args, **kwargs):
            nonlocal field
            if field is None:
                req: Request = args[0]
                if not isinstance(req, Request):
                    raise ValueError(REQUEST_ARGS_ERROR_MSG)
                field = req.app.get_conf("DEFAULT_RESPONSE_DATA_FIELD")
            res = await run_sync_or_async(handler, *args, **kwargs)
            try:
                res: Response = args[1]
                if not isinstance(res, Response):
                    raise ValueError(RESPONSE_ARGS_ERROR_MSG)
                if field not in res.body:
                    return res
                res.body[field] = schema(many=many).dump(res.body[field])
                if status_code is not None:
                    res.status(status_code)
                return res
            except ValidationError as exc:
                raise SchemaValidationError(exc.messages) from exc
            except TypeError as exc:
                raise exc
        route_data: dict = getattr(wrapper, "is_route_handler", {})
        wrapper.is_route_handler = {
            **route_data,
            "openapi_response_schema": schema,
            "openapi_response_many": many,
            "openapi_response_code": status_code,
            "openapi_response_status_desc": status_desc
        }
        return wrapper
    return decorator

def exception_responses(responses: dict[Schema, list[int]]) -> Callable:
    """
    Registers exception responses for a route handler.
    Used to create OpenAPI specs.

    Example:
    ```
    @get("/")
    @exception_responses(ExceptionSchema: [404, 400]})
    async def route_handler(req: Request, res: Response):
        return res.json({"data": "some_value"}).status(200)
    ```
    """
    def decorator(handler) -> Callable:
        @wraps(handler)
        async def wrapper(*args, **kwargs):
            return await run_sync_or_async(handler, *args, **kwargs)
        route_data: dict = getattr(wrapper, "is_route_handler", {})
        wrapper.is_route_handler = {
            **route_data,
            "openapi_exception_responses": responses
        }
        return wrapper
    return decorator

def route_decorator_factory(method: str):
    """
    Returns a decorator that marks a function as a route handler
    for the given HTTP method.
    """
    def route(url_path: str, description: str = "", 
              summary: str = "", openapi_ignore: bool = False):
        def decorator(handler: Callable):
            @wraps(handler)
            async def wrapper(*args, **kwargs):
                if not getattr(handler, "parent_class", None):
                    module_name = handler.__module__  # e.g. "__main__" or some_module
                    module_obj = sys.modules[module_name]
                    # Now parse the class name out of __qualname__
                    class_name = handler.__qualname__.split('.')[0]
                    # Attempt to look it up in the module's global scope
                    parent_class = getattr(module_obj, class_name, None)
                    if parent_class is None:
                        raise ValueError(f"Failed to find class blueprint parent class of handler: {handler}")
                    handler.parent_class = parent_class
                if getattr(parent_class, "before_request_handlers", False):
                    for method in parent_class.before_request_handlers:
                        await run_sync_or_async(method, args[0])
                res = await run_sync_or_async(handler, *args, **kwargs)
                if getattr(parent_class, "after_request_handlers", False):
                    for method in parent_class.after_request_handlers:
                        await run_sync_or_async(method, res)
                return res
            route_data: dict = getattr(wrapper, "is_route_handler", {})
            is_route_handler = {
                **route_data,
                "method": method,
                "path": url_path,
                "description": description,
                "summary": summary,
            }
            handler.is_route_handler = is_route_handler
            wrapper.is_route_handler = is_route_handler
            wrapper.openapi_ignore = openapi_ignore
            return staticmethod(wrapper)
        return decorator
    return route

get: Callable = route_decorator_factory("GET")
post: Callable = route_decorator_factory("POST")
put: Callable = route_decorator_factory("PUT")
patch: Callable = route_decorator_factory("PATCH")
delete: Callable = route_decorator_factory("DELETE")

def websocket(path: str):
    """Decorator for websocket endpoints"""
    def decorator(handler: Callable):
        handler.is_websocket_handler = {
            "method": "websocket",
            "path": path
        }
        return staticmethod(handler)
    return decorator

def before_request():
    """
    Decorator for registering methods that should run before the
    route handler is executed. Methods are executed in the order they are appended
    to the list and get the same arguments and keyword arguments that would be passed to the
    route 
    
    Method shouldnt return anything. It should only performs modification
    on the request and/or response object
    """
    def decorator(func: Callable):
        func.is_before_request_handler = True
        return func
    return staticmethod(decorator)

def after_request():
    """
    Decorator for registering methods that should run before the
    route handler is executed. Methods are executed in the order they are appended
    to the list and get the same arguments and keyword arguments that would be passed to the
    route 
    
    Method shouldnt return anything. It should only performs modification
    on the request and/or response object
    """
    def decorator(func: Callable):
        func.is_after_request_handler = True
        return func
    return staticmethod(decorator)

class ClassBlueprint:
    """
    Base class for ClassBlueprint
    """
    router: Router = None
    websockets_router: Router = None
    openapi_registry: dict = None
    before_request_handlers: list[Callable] = None
    after_request_handlers: list[Callable] = None

    SCHEMA_LOCATION_MAPPINGS: dict[str, str] = {
        "json": "application/json",
        "form": "application/x-www-form-urlencoded",
        "files": "multipart/form-data",
        "form_and_files": "multipart/form-data",
        "query": "query"
    }

    @classmethod
    def _get_router(cls) -> Router:
        """
        Returns the class router instance
        """
        if cls.router is None:
            raise MissingRouterInstance()
        return cls.router
    
    @classmethod
    def _get_websockets_router(cls) -> Router:
        """
        Returns the class websockets router instance
        """
        if cls.websockets_router is None:
            raise MissingRouterInstance()
        return cls.websockets_router

    @classmethod
    def _add_route_function(cls, handler: Callable):
        """
        Adds route handler to router
        """
        handler_data: dict = getattr(handler, "is_route_handler", None)
        handler.is_route_handler = {
            **handler_data,
            "host_blueprint": cls
        }
        if handler_data is None:
            raise InvalidRouteHandler()
        cls.router.add_route(handler_data["path"],
                             handler,
                             [handler_data["method"]])
    
    @classmethod
    def _add_websocket_function(cls, handler: Callable):
        """
        Adds websocket handler to websocket router
        """ 
        handler_data: dict = getattr(handler, "is_websocket_handler", None)
        if handler_data is None:
            raise InvalidWebsocketHandler()
        cls.websockets_router.add_route(handler_data["path"],
                             handler,
                             [handler_data["method"]])

    @classmethod
    def _add_before_request_handler(cls, handler: Callable):
        """
        Adds before request handler to list
        """
        if cls.before_request_handlers is None:
            cls.before_request_handlers = []
        cls.before_request_handlers.append(handler)

    @classmethod
    def _add_after_request_handler(cls, handler: Callable):
        """
        Adds after request handler to list
        """
        if cls.after_request_handlers is None:
            cls.after_request_handlers = []
        cls.after_request_handlers.append(handler)

    @classmethod
    def _collect_openapi_data(cls, handler: Callable):
        """
        Collects openApi data and stores it to the 
        openapi_registry data:
        """
        # Meta data attached by @input/@output decorators

        handler_data = getattr(handler, "is_route_handler", None)
        if handler_data is None:
            return
        method: str = handler_data["method"]
        path: str = handler_data["path"]
        summary: str = handler_data["summary"]
        description: str = handler_data["description"]
        openapi_request_schema = handler_data.get("openapi_request_schema", None)
        openapi_request_location = handler_data.get("openapi_request_location", None)
        openapi_response_schema = handler_data.get("openapi_response_schema", None)
        openapi_response_many = handler_data.get("openapi_response_many", False)
        openapi_response_code = handler_data.get("openapi_response_code", 200)
        openapi_response_status_desc = handler_data.get("openapi_response_status_desc", "OK")
        openapi_exception_responses = handler_data.get("openapi_exception_responses", None)

        if method not in cls.openapi_registry:
            cls.openapi_registry[method] = {}
        
        if hasattr(cls, "blueprint_name"):
            path = getattr(cls, "url_prefix") + path

        cls.openapi_registry[method][path] = {
            "operation_id": handler.__name__,
            "summary": summary,
            "description": description,
            "request_schema": openapi_request_schema,
            "request_location": cls.SCHEMA_LOCATION_MAPPINGS.get(openapi_request_location),
            "response_schema": openapi_response_schema,
            "response_code": openapi_response_code,
            "response_many": openapi_response_many,
            "response_description": openapi_response_status_desc,
            "exception_responses": openapi_exception_responses
        }
    
    @classmethod
    def add_app(cls, app):
        """
        Adds app instance to class blueprint
        For compatibility with standard blueprints and application routes
        """
        cls.app = app


def blueprint(import_name: str, blueprint_name: str, 
              url_prefix: str = "", static_folder_path: str = None):
    """
    Decorator to turn a class into a ClassBlueprint
    Adds the ClassBlueprint class as a Parent class
    of the decorated class
    """
    def decorator(cls):
        # Create a new class that inherits from 'parent_cls' 
        # and *also* the original bases of 'cls' (if any).
        new_cls = type(
            cls.__name__,
            (ClassBlueprint,) + cls.__bases__,   # new bases
            dict(cls.__dict__)              # copy original class attributes
        )

        # Copy the module name to make debugging / introspection nicer.
        new_cls.__module__ = cls.__module__
        new_cls.import_name = import_name
        new_cls.blueprint_name = blueprint_name
        new_cls.url_prefix = url_prefix
        new_cls.static_folder_path = static_folder_path
        new_cls.router = Router()
        new_cls.websockets_router = Router()
        new_cls.openapi_registry = {}
        new_cls._before_request_methods = []
        new_cls._after_request_methods = []
        for name, attr in list(new_cls.__dict__.items()):
            if callable(attr) and isinstance(attr, staticmethod):
                if hasattr(attr.__func__, "is_route_handler"):
                    handler = getattr(new_cls, name)
                    new_cls._add_route_function(handler)
                    if not getattr(handler, "openapi_ignore"):
                        new_cls._collect_openapi_data(handler)
                if hasattr(attr.__func__, "is_websocket_handler"):
                    handler = getattr(new_cls, name)
                    new_cls._add_websocket_function(handler)
            if(getattr(attr, "is_before_request_handler", False)):
                new_cls._add_before_request_handler(attr)
            if(getattr(attr, "is_after_request_handler", False)):
                new_cls._add_after_request_handler(attr)

        return new_cls
    return decorator
