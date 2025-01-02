"""
Common class which is used to extend the PyJolt and Blueprint class
"""
from functools import wraps
from typing import Callable
from marshmallow import Schema, ValidationError
from .exceptions import MissingRequestData, SchemaValidationError
from .request import Request
from .response import Response

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

    # Routing decorators [GET; POST; PUT; PATCH; DELETE]
    def get(self, path: str):
        """Decorator for GET endpoints with path variables support."""
        def decorator(func: Callable):
            self._add_route_function("GET", path, func)
            return func
        return decorator

    def post(self, path: str):
        """Decorator for POST endpoints with path variables support."""
        def decorator(func: Callable):
            self._add_route_function("POST", path, func)
            return func
        return decorator

    def put(self, path: str):
        """Decorator for PUT endpoints with path variables support."""
        def decorator(func: Callable):
            self._add_route_function("PUT", path, func)
            return func
        return decorator

    def patch(self, path: str):
        """Decorator for PATCH endpoints with path variables support."""
        def decorator(func: Callable):
            self._add_route_function("PATCH", path, func)
            return func
        return decorator

    def delete(self, path: str):
        """Decorator for DELETE endpoints with path variables support."""
        def decorator(func: Callable):
            self._add_route_function("DELETE", path, func)
            return func
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
        allowed_location: list[str] = ["json", "form", "files", "form_and_files"]
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
                return await handler(*args, **kwargs)
            return wrapper
        return decorator

    def output(self, schema: Schema,
              many: bool = False,
              status_code: int = 200,
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
                result: dict[str, any] = await handler(*args, **kwargs)
                if result is None or isinstance(result, Response):
                    return
                if field not in result:
                    raise KeyError(f"Key {field} not present in return of route handler")
                try:
                    json_data = schema(many=many).dump(result[field])
                    result[field] = json_data
                    res: Response = args[1]
                    if not isinstance(res, Response):
                        raise ValueError(self.RESPONSE_ARGS_ERROR_MSG)
                    res.json(result).status(status_code)
                    return
                except ValidationError as exc:
                    # pylint: disable-next=W0707
                    raise SchemaValidationError(exc.messages)
                    #pylint: disable-next=W0706
                except TypeError:
                    raise

            return wrapper
        return decorator
