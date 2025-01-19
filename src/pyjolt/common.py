"""
Common class which is used to extend the PyJolt and Blueprint class
"""
from functools import wraps
from typing import Callable
from marshmallow import Schema, ValidationError
from .exceptions import MissingRequestData, SchemaValidationError
from .request import Request
from .response import Response
from .router import Router
from .utilities import run_sync_or_async

class Common:
    """
    Common class which contains methods common to the PyJolt class and 
    Blueprint class.
    """

    REQUEST_ARGS_ERROR_MSG: str = ("Injected argument 'req' of route handler is not an instance "
                        "of the Request class. If you used additional decorators "
                        "or middleware handlers make sure the order of arguments "
                        "was not changed. The Request and Response arguments "
                        "must always come first.")
    
    RESPONSE_ARGS_ERROR_MSG: str = ()

    SCHEMA_LOCATION_MAPPINGS: dict[str, str] = {
        "json": "application/json",
        "form": "application/x-www-form-urlencoded",
        "files": "multipart/form-data",
        "form_and_files": "multipart/form-data",
        "query": "query"
    }

    def __init__(self):
        self.router = Router()
        self.openapi_registry = {}
        self._before_request_methods = []
        self._after_request_methods = []
    
    def add_before_request_method(self, func: Callable):
        """
        Adds method to before request collection
        """
        self._before_request_methods.append(func)
    
    def add_after_request_method(self, func: Callable):
        """
        Adds method to before request collection
        """
        self._after_request_methods.append(func)
    
    @property
    def before_request(self):
        """
        Decorator for registering methods that should after before the
        route handler is executed. Methods are executed in the order they are appended
        to the list and get the same arguments and keyword arguments that would be passed to the
        route 
        
        Method shouldnt return anything. It should only performs modification
        on the request and/or response object
        """
        def decorator(func: Callable):
            self.add_before_request_method(func)
            return func
        return decorator

    @property
    def after_request(self):
        """
        Decorator for registering methods that should after before the
        route handler is executed. Methods are executed in the order they are appended
        to the list and get the same arguments and keyword arguments that would be passed to the
        route handler

        Method shouldnt return anything. It should only performs modification
        on the request and/or response object
        """
        def decorator(func: Callable):
            self.add_after_request_method(func)
            return func
        return decorator
    
    def _collect_openapi_data(self, method: str, path: str,
                              description: str, summary: str, func: Callable):
        """
        Collects openApi data and stores it to the 
        openapi_registry data:
        """
        # Meta data attached by @input/@output decorators
        openapi_request_schema = getattr(func, "openapi_request_schema", None)
        openapi_request_location = getattr(func, "openapi_request_location", None)
        openapi_response_schema = getattr(func, "openapi_response_schema", None)
        openapi_response_many = getattr(func, "openapi_response_many", False)
        openapi_response_code = getattr(func, "openapi_response_code", 200)
        openapi_response_status_desc = getattr(func, "openapi_response_status_desc", "OK")

        if method not in self.openapi_registry:
            self.openapi_registry[method] = {}
        
        if hasattr(self, "blueprint_name"):
            path = getattr(self, "url_prefix") + path

        self.openapi_registry[method][path] = {
            "operation_id": func.__name__,
            "summary": summary,
            "description": description,
            "request_schema": openapi_request_schema,
            "request_location": self.SCHEMA_LOCATION_MAPPINGS.get(openapi_request_location),
            "response_schema": openapi_response_schema,
            "response_code": openapi_response_code,
            "response_many": openapi_response_many,
            "response_description": openapi_response_status_desc
        }
    
    def get(self, path: str, description: str = "", summary: str = ""):
        """
        Registers a handler for GET request to the provided path.
        """

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                #runs before request methods
                for method in self._before_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
                #runs route handler
                await run_sync_or_async(func, *args, **kwargs)
                #runs after request methods
                for method in self._after_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
            self._add_route_function("GET", path, wrapper)
            self._collect_openapi_data("GET", path, description, summary, wrapper)
            return wrapper
        return decorator

    def post(self, path: str, description: str = "", summary: str = ""):
        """Decorator for POST endpoints with path variables support."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                #runs before request methods
                for method in self._before_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
                #runs route handler
                await run_sync_or_async(func, *args, **kwargs)
                #runs after request methods
                for method in self._after_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
            self._add_route_function("POST", path, wrapper)
            self._collect_openapi_data("POST", path, description, summary, wrapper)
            return wrapper
        return decorator

    def put(self, path: str, description: str = "", summary: str = ""):
        """Decorator for PUT endpoints with path variables support."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                #runs before request methods
                for method in self._before_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
                #runs route handler
                await run_sync_or_async(func, *args, **kwargs)
                #runs after request methods
                for method in self._after_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
            self._add_route_function("PUT", path, wrapper)
            self._collect_openapi_data("PUT", path, description, summary, wrapper)
            return wrapper
        return decorator

    def patch(self, path: str, description: str = "", summary: str = ""):
        """Decorator for PATCH endpoints with path variables support."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                #runs before request methods
                for method in self._before_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
                #runs route handler
                await run_sync_or_async(func, *args, **kwargs)
                #runs after request methods
                for method in self._after_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
            self._add_route_function("PATCH", path, wrapper)
            self._collect_openapi_data("PATCH", path, description, summary, wrapper)
            return wrapper
        return decorator

    def delete(self, path: str, description: str = "", summary: str = ""):
        """Decorator for DELETE endpoints with path variables support."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                #runs before request methods
                for method in self._before_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
                #runs route handler
                await run_sync_or_async(func, *args, **kwargs)
                #runs after request methods
                for method in self._after_request_methods:
                    await run_sync_or_async(method, *args, **kwargs)
            self._add_route_function("DELETE", path, wrapper)
            self._collect_openapi_data("DELETE", path, description, summary, wrapper)
            return wrapper
        return decorator

    def _add_route_function(self, method: str, path: str, func: Callable):
        """
        Adds the function to the Router.
        Raises DuplicateRoutePath if a route with the same (method, path) is already registered.
        """
        try:
            self.router.add_route(path, func, [method])
        except Exception as e:
            # Detect more specific errors?
            raise e

    def input(self, schema: Schema,
              many: bool = False,
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
                    raise ValueError(self.REQUEST_ARGS_ERROR_MSG)
                data = await req.get_data(location)
                if data is None:
                    raise MissingRequestData(f"Missing {location} request data.")
                try:
                    kwargs[f"{location}_data"] = schema(many=many).load(data)
                except ValidationError as err:
                    # pylint: disable-next=W0707
                    raise SchemaValidationError(err.messages)
                return await run_sync_or_async(handler, *args, **kwargs)
            wrapper.openapi_request_schema = schema # stores the Marshmallow schema
            wrapper.openapi_request_location = location # sets data location e.g., "json", "form", etc.
            return wrapper
        return decorator

    def output(self, schema: Schema,
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
                        raise ValueError(self.REQUEST_ARGS_ERROR_MSG)
                    field = req.app.get_conf("DEFAULT_RESPONSE_DATA_FIELD")
                await run_sync_or_async(handler, *args, **kwargs)
                try:
                    res: Response = args[1]
                    if not isinstance(res, Response):
                        raise ValueError(self.RESPONSE_ARGS_ERROR_MSG)
                    if field not in res.body:
                        return
                    res.body[field] = schema(many=many).dump(res.body[field])
                    if status_code is not None:
                        res.status(status_code)
                    return
                except ValidationError as exc:
                    raise SchemaValidationError(exc.messages) from exc
                except TypeError as exc:
                    raise exc
            wrapper.openapi_response_schema = schema
            wrapper.openapi_response_many = many
            wrapper.openapi_response_code = status_code
            wrapper.openapi_response_status_desc = status_desc
            return wrapper
        return decorator
