"""
Common class which is used to extend the PyJolt and Blueprint class
"""
import inspect
from functools import wraps
from typing import Callable, Type
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from .exceptions import (MissingRequestData, SchemaValidationError,
                         MissingDependencyInjectionMethod, PydanticSchemaValidationError)
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
        self.websockets_router = Router()
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
        Decorator for registering methods that should run before the
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
    
    def inject(self, **injected_args: dict[str, Type]) -> Callable:
        """
        A generic decorator that injects instances of the specified types into the decorated function.

        Args:
            injected_args: Keyword arguments where the key is the argument name to inject,
                        and the value is the type to inject.

        Returns:
            A decorator that injects the specified types into the decorated function.
        """
        def decorator(handler: Callable) -> Callable:
            @wraps(handler)
            async def wrapper(*args, **kwargs) -> any:
                # Inject instances for each specified argument
                for arg_name, arg_type in injected_args.items():
                    # Assume that `arg_type` is callable and can be instantiated
                    # Replace this with a more sophisticated logic if necessary
                    #kwargs[arg_name] = arg_type()  # Replace with your factory/logic if needed
                    injection_method: Callable = self.app.dependency_injection_map(arg_type.__name__)
                    if injection_method is None:
                        raise MissingDependencyInjectionMethod(arg_type)
                    kwargs[arg_name] = await run_sync_or_async(injection_method)

                # Call the original handler with injected arguments
                return await run_sync_or_async(handler, *args, **kwargs)

            return wrapper
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
        openapi_exception_responses = getattr(func, "openapi_exception_responses", None)

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
            "response_description": openapi_response_status_desc,
            "exception_responses": openapi_exception_responses
        }
    
    def get(self, path: str, response_schema: BaseModel = None, many: bool = False,
            status_code: int = 200, status_desc: str = None, field: str = None,
            description: str = "", summary: str = "", openapi_ignore: bool = False):
        """
        Registers a handler for GET request to the provided path.
        """

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                #runs before request methods
                req: Request = args[0]
                for method in self._before_request_methods:
                    await run_sync_or_async(method, req)
                #runs route handler
                res: Response = await run_sync_or_async(func, *args, **kwargs)
                if response_schema is not None:
                    default_field = req.app.get_conf("DEFAULT_RESPONSE_DATA_FIELD", None)
                    data_field: str = field if field is not None else default_field if default_field is not None else None
                    response_data = None
                    if data_field is not None:
                        response_data = response_schema(**res.body.get(data_field)) if many is False else [response_schema(**item) for item in res.body.get(data_field)]
                        res.body[field] = response_data
                    else:
                        response_data = response_schema(**res.body) if many is False else [response_schema(**item) for item in res.body]
                        res.body = response_data

                    if status_code is not None:
                        res.status(status_code)
                #runs after request methods
                for method in self._after_request_methods:
                    res = await run_sync_or_async(method, res)
                return res
            self._add_route_function("GET", path, wrapper)

            if openapi_ignore is False:
                wrapper.openapi_response_schema = response_schema
                wrapper.openapi_response_many = many
                wrapper.openapi_response_code = status_code
                wrapper.openapi_response_status_desc = status_desc
                self._collect_openapi_data("GET", path, description, summary, wrapper)
            return wrapper
        return decorator

    def _make_method_decorator(self, http_method: str, path: str,
                               response_schema: BaseModel = None,
                               many: bool = False,
                               status_code: int = 200,
                               status_desc: str = None,
                               field: str = None,
                               description: str = "",
                               summary: str = "",
                               openapi_ignore: bool = False):
        """
        Internal factory that returns a decorator for the given HTTP method (e.g. "POST").
        It includes the logic to:
          - Inspect for Pydantic model parameters
          - Load request data
          - Run before/after request hooks
          - Collect OpenAPI data
        """

        def decorator(func: Callable):
            # 1) Checks if pydantic parameters are present in method signature
            signature = inspect.signature(func)
            pydantic_params = {}
            for param_name, param_obj in signature.parameters.items():
                param_type = param_obj.annotation
                # If a parameter is a subclass of Pydantic BaseModel
                if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                    location: str = param_type.__location__
                    allowed_location: list[str] = ["json", "form", "files", "form_and_files", "query"]
                    if location not in allowed_location:
                        raise ValueError(f"Input data location of endpoint [{http_method}]({path})  "
                                         f"must be one of: {allowed_location}")
                    pydantic_params[param_name] = param_type

            @wraps(func)
            async def wrapper(*args, **kwargs):
                # The first positional arg (args[0]) is assumed to be 'req' (Request)
                req: Request = args[0]
                # 2) Run any "before request" methods
                for method in self._before_request_methods:
                    await run_sync_or_async(method, req)

                # 3) If a pydantic schema is present in the method parameters
                if pydantic_params:
                    for param_name, schema_cls in pydantic_params.items():
                        # Location of incoming data (json, form, files, form_and_files, query)
                        data = await req.get_data(location=schema_cls.__location__)
                        if data is None:
                            raise MissingRequestData(
                                f"Missing {schema_cls.__location__} request data."
                            )
                        try:
                            #Loads data into Pydantic schema
                            loaded_data = schema_cls(**data)
                            kwargs[param_name] = loaded_data
                        except PydanticValidationError as err:
                            #If loading into pydantic schema failes a SchemaValidationError is raised
                            #with validation errors
                            #pylint: disable-next=W0707
                            raise PydanticSchemaValidationError(
                                err.errors(include_input=False,
                                           include_url=False,
                                           include_context=False)
                            )

                # 4) Execute the main route handler
                res: Response = await run_sync_or_async(func, *args, **kwargs)

                if response_schema is not None:
                    cfg = getattr(response_schema, "model_config", {})
                    from_attr = cfg.get("from_attributes", False)
                    default_field = req.app.get_conf("DEFAULT_RESPONSE_DATA_FIELD", None)
                    data_field: str = field if field is not None else default_field if default_field is not None else None
                    response_data = None
                    if data_field is not None:
                        #response_data = response_schema(**res.body.get(data_field)) if many is False else [response_schema(**item) for item in res.body.get(data_field)]
                        if from_attr:
                            response_data = response_schema.model_validate(res.body.get(data_field)).model_dump() if many is False else [response_schema.model_validate(item).model_dump() for item in res.body.get(data_field)]
                        else:
                            response_data = response_schema.model_validate(res.body.get(data_field)) if many is False else [response_schema.model_validate(item) for item in res.body.get(data_field)]
                        res.body[field] = response_data
                    else:
                        if(from_attr):
                            response_data = response_schema.model_validate(res.body).model_dump() if many is False else [response_schema.model_validate(item).model_dump() for item in res.body]
                        else:
                            response_data = response_schema.model_validate(res.body) if many is False else [response_schema.model_validate(item) for item in res.body]
                        res.body = response_data

                    if status_code is not None:
                        res.status(status_code)

                # 5) Run any "after request" methods
                for method in self._after_request_methods:
                    res = await run_sync_or_async(method, res)

                return res

            # Register the route
            self._add_route_function(http_method, path, wrapper)

            # Register OpenAPI metadata if not ignored
            if openapi_ignore is False:
                if pydantic_params:
                    #pylint: disable-next=W0644
                    schema_cls, = pydantic_params.values()
                    wrapper.openapi_request_schema = schema_cls # stores the Pydantic schema
                    wrapper.openapi_request_location = schema_cls.__location__ # sets data location e.g., "json", "form", etc.
                wrapper.openapi_response_schema = response_schema
                wrapper.openapi_response_many = many
                wrapper.openapi_response_code = status_code
                wrapper.openapi_response_status_desc = status_desc
                self._collect_openapi_data(http_method, path, description, summary, wrapper)

            return wrapper

        return decorator

    # --------------------------------------------------------------------------
    # Decorators: POST, PUT, PATCH, DELETE
    # --------------------------------------------------------------------------

    def post(self, path: str,
             response_schema: BaseModel = None,
             many: bool = False,
             status_code: int = 200,
             status_desc: str = None,
             field: str = None,
             description: str = "",
             summary: str = "",
             openapi_ignore: bool = False):
        """
        Decorator for POST endpoints with path variables support.
        Also handles automatically loading request data into any
        Pydantic model parameters on the endpoint function.
        """
        return self._make_method_decorator(
            http_method="POST",
            path=path,
            response_schema=response_schema,
            many=many,
            status_code=status_code,
            status_desc=status_desc,
            field=field,
            description=description,
            summary=summary,
            openapi_ignore=openapi_ignore
        )

    def put(self, path: str,
            response_schema: BaseModel = None,
            many: bool = False,
            status_code: int = 200,
            status_desc: str = None,
            field: str = None,
            description: str = "",
            summary: str = "",
            openapi_ignore: bool = False):
        """
        Decorator for PUT endpoints with path variables support.
        Includes the same Pydantic data-loading logic as POST.
        """
        return self._make_method_decorator(
            http_method="PUT",
            path=path,
            response_schema=response_schema,
            many=many,
            status_code=status_code,
            status_desc=status_desc,
            field=field,
            description=description,
            summary=summary,
            openapi_ignore=openapi_ignore
        )

    def patch(self, path: str,
              response_schema: BaseModel = None,
              many: bool = False,
              status_code: int = 200,
              status_desc: str = None,
              field: str = None,
              description: str = "",
              summary: str = "",
              openapi_ignore: bool = False):
        """
        Decorator for PATCH endpoints with path variables support.
        Includes the same Pydantic data-loading logic as POST.
        """
        return self._make_method_decorator(
            http_method="PATCH",
            path=path,
            response_schema=response_schema,
            many=many,
            status_code=status_code,
            status_desc=status_desc,
            field=field,
            description=description,
            summary=summary,
            openapi_ignore=openapi_ignore
        )

    def delete(self, path: str,
               response_schema: BaseModel = None,
               many: bool = False,
               status_code: int = 200,
               status_desc: str = None,
               field: str = None,
               description: str = "",
               summary: str = "",
               openapi_ignore: bool = False):
        """
        Decorator for DELETE endpoints with path variables support.
        Includes the same Pydantic data-loading logic as POST.
        """
        return self._make_method_decorator(
            http_method="DELETE",
            path=path,
            response_schema=response_schema,
            many=many,
            status_code=status_code,
            status_desc=status_desc,
            field=field,
            description=description,
            summary=summary,
            openapi_ignore=openapi_ignore
        )

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

    def websocket(self, path: str):
        """Decorator for websocket endpoints"""
        def decorator(func: Callable):
            self.websockets_router.add_route(path, func, ["websocket"])
            return func
        return decorator
    
    def exception_responses(self, responses: dict[BaseModel, list[int]]) -> Callable:
        """
        Registers exception responses for a route handler.
        Used to create OpenAPI specs.

        Example:
        ```
        @app.get("/")
        @app.exception_responses(ExceptionSchema: [404, 400]})
        async def route_handler(req: Request, res: Response):
            return res.json({"data": "some_value"}).status(200)
        ```
        """
        def decorator(handler) -> Callable:
            @wraps(handler)
            async def wrapper(*args, **kwargs):
                return await run_sync_or_async(handler, *args, **kwargs)
            wrapper.openapi_exception_responses = responses # stores the Marshmallow schemas
            return wrapper
        return decorator

    def output(self, schema: BaseModel,
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
                res = await run_sync_or_async(handler, *args, **kwargs)
                try:
                    if not isinstance(res, Response):
                        raise ValueError(self.RESPONSE_ARGS_ERROR_MSG)
                    if field not in res.body:
                        return res
                    res.body[field] = schema.model_validate(res.body.get(field)).model_dump() if many is False else [schema.model_validate(item).model_dump() for item in res.body.get(field)]
                    if status_code is not None:
                        res.status(status_code)
                    return res
                except PydanticSchemaValidationError as exc:
                    raise SchemaValidationError(exc.message) from exc
                except TypeError as exc:
                    raise exc
            wrapper.openapi_response_schema = schema
            wrapper.openapi_response_many = many
            wrapper.openapi_response_code = status_code
            wrapper.openapi_response_status_desc = status_desc
            return wrapper
        return decorator
