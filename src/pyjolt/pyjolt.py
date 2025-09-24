"""
PyJolt application class
"""
# mypy: check-untyped-defs = True
import argparse
import json
from typing import Any, Callable, Optional, TYPE_CHECKING, Type
import aiofiles
from dotenv import load_dotenv
from loguru import logger, Logger
from werkzeug.exceptions import NotFound, MethodNotAllowed
from pydantic import BaseModel, ValidationError

from .exceptions.http_exceptions import HtmlAborterException, AborterException
from .http_statuses import HttpStatus
from .request import Request
from .response import Response
from .utilities import get_app_root_path, run_sync_or_async
from .exceptions import BaseHttpException, CustomException
from .router import Router
from .static import Static
from .open_api import OpenAPIController
from .controller import path

if TYPE_CHECKING:
    from .controller import Controller
    from .exceptions import ExceptionHandler

# ──────────────────────────────────────────────────────────────────────────────
# Monkey‐patch Uvicorn’s RequestResponseCycle.run_asgi so that, just before
# it invokes your ASGI app, it injects the real socket into the scope dict.
try:
    from uvicorn.protocols.http.h11_impl import RequestResponseCycle

    _orig_run_asgi = RequestResponseCycle.run_asgi

    async def _patched_run_asgi(self, app):
        # grab the raw socket from the transport and stash it into scope
        sock = None
        if hasattr(self, "transport") and self.transport is not None:
            sock = self.transport.get_extra_info("socket")
        if sock is not None:
            self.scope["socket"] = sock

        # now call the real ASGI loop
        return await _orig_run_asgi(self, app)

    RequestResponseCycle.run_asgi = _patched_run_asgi
# pylint: disable-next=W0718
except Exception as e:
    logger.debug(
        "Could not patch RequestResponseCycle.run_asgi; "
        "os.sendfile() zero-copy will fall back to aiofiles. "
        f"Patch error: {e}"
    )
# ──────────────────────────────────────────────────────────────────────────────


class PyJolt:
    """PyJolt class implementation. Used to create a new application instance"""

    DEFAULT_CONFIGS: dict[str, Any] = {
        "APP_NAME": "PyJolt",
        "VERSION": "1.0",
        "LOGGER_NAME": "Logger",
        "TEMPLATES_DIR": "/templates",
        "STATIC_DIR": "/static",
        "STATIC_URL": "/static",
        "TEMPLATES_STRICT": True,
        "STRICT_SLASHES": False,
        "OPEN_API": True,
        "OPEN_API_URL": "/openapi",
        "OPEN_API_DESCRIPTION": "Simple API",
    }

    def __init__(
        self,
        import_name: str,
        env_path: Optional[str] = None,
    ):
        """Init function"""
        self._is_built = False

        if env_path is not None:
            self._load_env(env_path)
        self._root_path = get_app_root_path(import_name)
        # Dictionary which holds application configurations
        self._configs = {**self.DEFAULT_CONFIGS}
        self._static_files_path = f"{self._root_path + self.get_conf('STATIC_DIR')}"
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")
        self._router = Router(self.get_conf("STRICT_SLASHES", False))
        self._logger = logger

        self._app = self._base_app
        self._middleware: list[Callable] = []
        self._controllers: dict[str, "Controller"] = {}
        self._exception_handlers: dict[str, Callable] = {}
        self._json_spec: Optional[dict] = None

        self._extensions: dict = {}
        self.global_context_methods: list[Callable] = []

        self._on_startup_methods: list[Callable] = []
        self._on_shutdown_methods: list[Callable] = []

        self.cli = argparse.ArgumentParser(description="PyJolt CLI")
        self.subparsers = self.cli.add_subparsers(dest="command", help="CLI commands")
        self.cli_commands: dict = {}

    def _load_env(self, env_path: str):
        """
        Loads environment variables from <name>.env file
        """
        load_dotenv(dotenv_path=env_path, verbose=True)

    def configure_app(self, configs: object | dict):
        """
        Configures application with provided configuration class or dictionary
        """
        if isinstance(configs, dict):
            self._configure_from_dict(configs)
        if isinstance(configs, object):
            self._configure_from_class(configs)

        # Sets new variables after configuring with object|dict
        self._static_files_path = f"{self._root_path + self.get_conf('STATIC_DIR')}"
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")

    def _configure_from_class(self, configs: object):
        """
        Configures application from object/class
        """
        for config_name in dir(configs):
            self._configs[config_name] = getattr(configs, config_name)

    def _configure_from_dict(self, configs: dict[str, Any]):
        """
        Configures application from dictionary
        """
        for key, value in configs.items():
            self._configs[key] = value

    def get_conf(self, config_name: str, default: Any = None) -> Any:
        """
        Returns app configuration with provided config_name.
        Raises error if configuration is not found.
        """
        if config_name in self.configs:
            return self.configs[config_name]
        return default

    def add_global_context_method(self, func: Callable):
        """
        Adds global context method to global_context_methods array
        """
        self.global_context_methods.append(func)

    async def _base_app(self, req: Request, send):
        """
        The bare-bones application without any middleware.
        """
        try:
            try:
                res: Response = await run_sync_or_async(
                    req.route_handler, req, **req.route_parameters
                )
                response_type: Optional[Type[Any]] = req.response.expected_body_type()
                return await self.send_response(res, send, response_type)
            except AborterException as exc:
                req.res.json({
                    "message": exc.message,
                    "status": exc.status,
                    "data": exc.data
                }).status(exc.status_code)
                return await self.send_response(req.res, send, exc.__class__)
            except HtmlAborterException as exc:
                res = (await req.res.html(exc.template, context=exc.data)).status(exc.status_code)
                return await self.send_response(res, send, None)
            except (CustomException, BaseHttpException, ValidationError) as exc:
                handler = self._exception_handlers.get(exc.__class__.__name__, None) or None
                if not handler:
                    raise Exception("Unhandled exception occured") from exc
                res = await run_sync_or_async(handler, req, exc)
                response_type = res.expected_body_type() or exc.__class__
                return await self.send_response(res, send, response_type)
            # pylint: disable-next=W0718
            except Exception:
                raise
        # pylint: disable-next=W0718
        except Exception as exc:
            #Catches every error and returns internal server error message
            #if the app is in production (DEBUG = False)
            #else reraises the error
            if not self.get_conf("DEBUG", False):
                res = req.res.json({
                    "status": "error",
                    "message": "Internal server error",
                }).status(HttpStatus.INTERNAL_SERVER_ERROR)
                return await self.send_response(res, send, Exception)
            raise

    async def abort_route_not_found(self, send):
        """
        Aborts request because route was not found
        """
        # 404 - endpoint not found error
        await send(
            {
                "type": "http.response.start",
                "status": 404,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b'{ "status": "error", "message": "Endpoint not found" }',
            }
        )

    async def send_response(self, res: Response, send, response_type: Optional[Type[Any]] = None):
        """
        Sends response
        """
        # Build headers for ASGI send
        headers = []
        for k, v in res.headers.items():
            headers.append((k.encode("utf-8"), v.encode("utf-8")))
        await send(
            {
                "type": "http.response.start",
                "status": res.status_code.value if isinstance(res.status_code, HttpStatus) else res.status_code,
                "headers": headers,
            }
        )
        # Zero-copy _parameters_ were stashed in res._zero_copy
        if res.zero_copy is not None:
            params = res.zero_copy
            file_path = params["file_path"]
            start = params["start"]
            length = params["length"]

            # stream in 1 MiB chunks
            chunk_size = 24 * 1024 * 1024
            remaining = length

            async with aiofiles.open(file_path, "rb") as f:
                await f.seek(start)
                while remaining > 0:
                    to_read = min(remaining, chunk_size)
                    chunk = await f.read(to_read)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    await send(
                        {
                            "type": "http.response.body",
                            "body": chunk,
                            "more_body": remaining > 0,
                        }
                    )
            return
        if (response_type and issubclass(response_type, (CustomException, BaseHttpException, Exception)) 
            and not issubclass(response_type, HtmlAborterException)):
            res.body = json.dumps(res.body).encode("utf-8")
        elif response_type and res.body and issubclass(response_type, BaseModel) and isinstance(res.body, dict):
            res.body = response_type(**res.body).model_dump_json().encode("utf-8")
        elif response_type and res.body and issubclass(response_type, BaseModel) and isinstance(res.body, BaseModel):
            res.body = res.body.model_dump_json().encode("utf-8")
        elif res.body and response_type is None and isinstance(res.body, BaseModel):
            #logger.warning("Returned body is an instance of BaseModel but the endpoint is not indicated to return this type. Please consider using a return type with () -> Response[T]:")
            res.body = res.body.model_dump_json().encode("utf-8")
        elif res.body and not isinstance(res.body, (bytes, bytearray)):
            #logger.warning("Returned body type is not indicated. Body will be serialized using json.dumps().encode('utf-8'). Please consider using a return type for serialization with () -> Response[T]:")
            res.body = json.dumps(res.body).encode("utf-8")

        await send(
            {
                "type": "http.response.body",
                "body": res.body or b"",
            }
        )

    async def _lifespan_app(self, _, receive, send):
        """This loop will listen for 'startup' and 'shutdown'"""
        while True:
            message = await receive()

            if message["type"] == "lifespan.startup":
                # Run all your before_start methods once
                for method in self._on_startup_methods:
                    await run_sync_or_async(method, self)

                # Signal uvicorn that startup is complete
                await send({"type": "lifespan.startup.complete"})

            elif message["type"] == "lifespan.shutdown":
                # Run your after_start methods (often used for cleanup)
                for method in self._on_shutdown_methods:
                    await run_sync_or_async(method, self)

                # Signal uvicorn that shutdown is complete
                await send({"type": "lifespan.shutdown.complete"})
                return  # Exit the lifespan loop

    async def _handle_http_request(self, scope, receive, send):
        """
        Handles http requests
        """
        # We have a matching route
        method: str = scope["method"]
        url_path: str = scope["path"]
        self._log_request(scope, method, url_path)
        route_handler, path_kwargs = self.router.match(url_path, method)
        if not route_handler:
            return await self.abort_route_not_found(send)
        req = Request(scope, receive, self, path_kwargs, route_handler)
        return await self._app(req, send)

    def _log_request(self, scope, method: str, url_path: str) -> None:
        """
        Logs incoming request
        """
        logger.info(
            f"HTTP request. CLIENT: {scope['client'][0]}, SCHEME: {scope['scheme']}, METHOD: {method}, PATH: {url_path}, QUERY_STRING: {scope['query_string'].decode('utf-8')}"
        )

    def register_static_controller(self, base_path: str):
        static_controller_dec = path(f"{base_path}", open_api_spec=False)
        static_controller = static_controller_dec(Static)
        self.register_controller(static_controller) # type: ignore
    
    def register_openapi_controller(self):
        openapi_controller_dec = path(self.get_conf("OPEN_API_URL"), open_api_spec=False)
        openapi_controller = openapi_controller_dec(OpenAPIController)
        self.register_controller(openapi_controller)

    def build(self) -> None:
        """
        Build the final app by wrapping self._app in all middleware.
        Apply them in reverse order so the first middleware in the list
        is the outermost layer.
        """
        self.register_static_controller(self.get_conf('STATIC_URL'))
        if self.get_conf("OPEN_API", False):
            self.build_openapi_spec()
            self.register_openapi_controller()
        app = self._base_app
        # for factory in reversed(self._middleware):
        #     app = factory(self, app)
        self._app = app
        self._is_built = True
    
    def add_extension(self, extension):
        """
        Adds extension to extension map
        """
        ext_name: str = (
            extension.__name__
            if hasattr(extension, "__name__")
            else extension.__class__.__name__
        )
        self._extensions[ext_name] = extension

    def _add_route_function(self, method: str, url_path: str, func: Callable, endpoint_name: str):
        """
        Adds the function to the Router.
        Raises DuplicateRoutePath if a route with the same (method, path) is already registered.
        """
        try:
            self.router.add_route(url_path, func, [method], endpoint_name)
        except Exception as e:
            # Detect more specific errors?
            raise e

    def register_controller(self, *ctrls: "type[Controller]"):
        """Registers controller class with application"""
        for ctrl in ctrls:
            ctrl_path: str = getattr(ctrl, "_controller_path")
            ctrl_open_api_spec = getattr(ctrl, "_include_open_api_spec")
            ctrl_open_api_tags = getattr(ctrl, "_open_api_tags", None)
            ctrl_instance = ctrl(self, ctrl_path, ctrl_open_api_spec, ctrl_open_api_tags)

            self._controllers[ctrl_instance.path] = ctrl_instance
            endpoint_methods: dict[str, dict[str, str|Callable]] = ctrl_instance.get_endpoint_methods()
            for http_method, endpoints in endpoint_methods.items():
                for url_path, method in endpoints.items():
                    method_name: Callable = method["method"].__name__ # type: ignore
                    #handler: Callable = getattr(ctrl_instance, method_name) # type: ignore
                    endpoint_name: str = f"{ctrl_instance.__class__.__name__}.{method_name}"
                    self._add_route_function(http_method,
                                            ctrl_instance.path+url_path,
                                            method["method"],
                                            endpoint_name)

    def register_exception_handler(self, *handlers: "type[ExceptionHandler]"):
        """Registers exception controller with application"""
        for handler in handlers:
            handler_instance = handler(self)
            handled_exceptions = handler_instance.get_exception_mapping()
            self._exception_handlers.update(handled_exceptions)

    def url_for(self, endpoint: str, **values) -> str:
        """
        Returns url for endpoint method
        :param endpoint: the name of the endpoint handler method namespaced
        with the blueprint name (if in blueprint)
        :param values: dynamic route parameters
        :return: url (string) for endpoint
        """
        adapter = self.router.url_map.bind("")  # Binds map to base url
        # If a value starts with a forward slash, systems like MacOS/Linux treat it as an absolute path
        try:
            return adapter.build(endpoint, values)
        except NotFound as exc:
            raise ValueError(f"Endpoint '{endpoint}' does not exist.") from exc
        except MethodNotAllowed as exc:
            raise ValueError(
                f"Endpoint '{endpoint}' exists but does not allow the method."
            ) from exc
        except Exception as exc:
            raise ValueError(
                f"Error building URL for endpoint '{endpoint}': {exc}"
            ) from exc
    
    def build_openapi_spec(self):
        """Builds open api spec"""
        from .open_api import build_openapi
        self._json_spec = build_openapi(self._controllers,
                                        title=self.app_name,
                                        version=self.version,
                                        openapi_version="3.0.3",
                                        servers=["http://localhost:8080"])
    
    def add_on_startup_method(self, func: Callable):
        """
        Adds method to on_startup collection
        """
        self._on_startup_methods.append(func)

    def add_on_shutdown_method(self, func: Callable):
        """
        Adds method to on_shutdown collection
        """
        self._on_shutdown_methods.append(func)
    
    def run_cli(self):
        """
        Executes the registered CLI commands.
        """
        args = self.cli.parse_args()
        if hasattr(args, "func"):
            args.func(args)  # pass the parsed arguments object
        else:
            self.cli.print_help()


    @property
    def json_spec(self) -> dict|None:
        return self._json_spec

    @property
    def router(self) -> Router:
        """Router instance property of the app"""
        return self._router

    @property
    def configs(self) -> dict[str, Any]:
        """
        Returns configuration dictionary
        """
        return self._configs

    @property
    def global_context(self):
        """
        Decorator registers method as a context provider for html templates.
        The return of the decorated function should be dictionary with key-value pairs.
        The returned dictionary is added to the context of the render_template method
        """

        def decorator(func: Callable):
            self.add_global_context_method(func)
            return func

        return decorator

    @property
    def root_path(self) -> str:
        """
        Returns root path of application
        """
        return self._root_path

    @property
    def app(self):
        """
        Returns self
        For compatibility with the Controller class
        which contains the app object on the app property
        """
        return self

    @property
    def static_files_path(self) -> str:
        """Static files paths"""
        return self._static_files_path

    @property
    def version(self) -> str:
        return self.get_conf("VERSION")

    @property
    def app_name(self) -> str:
        return self.get_conf("APP_NAME")
    
    @property
    def logger(self) -> Logger:
        return self._logger

    async def __call__(self, scope, receive, send):
        """
        Once built, __call__ just delegates to the fully wrapped app.
        """
        if not self._is_built:
            self.build()
        if scope["type"] == "lifespan":
            return await self._lifespan_app(scope, receive, send)
        if scope["type"] == "http":
            return await self._handle_http_request(scope, receive, send)
        raise ValueError(f"Unsupported scope type {scope['type']}")
