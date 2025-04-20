"""
pyjolt main class
"""
import argparse
import logging
import json
from typing import Any, Callable, Type
from dotenv import load_dotenv

from werkzeug.routing import Rule
from werkzeug.exceptions import NotFound, MethodNotAllowed
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined, Undefined

#from .exceptions import DuplicateRoutePath
from .common import Common
from .blueprint import Blueprint
from .request import Request
from .response import Response
from .utilities import get_app_root_path, run_sync_or_async
from .static import static
from .open_api import open_api_json_spec, open_api_swagger, OpenApiExtension
from .exceptions import (DuplicateExceptionHandler, MissingExtension, MissingRequestData,
                        StaticAssetNotFound, SchemaValidationError, PydanticSchemaValidationError,
                        AuthenticationException, InvalidJWTError, MissingResponseObject,
                        AborterException)


class PyJolt(Common, OpenApiExtension):
    """
    PyJolt ASGI server class, now using a Router for advanced path matching.
    """

    DEFAULT_CONFIGS: dict[str, any] = {
        "LOGGER_NAME": "PyJolt_logger",
        "TEMPLATES_DIR": "/templates",
        "STATIC_DIR": "/static",
        "STATIC_URL": "/static",
        "TEMPLATES_STRICT": "TEMPLATES_STRICT",
        "DEFAULT_RESPONSE_DATA_FIELD": "data",
        "STRICT_SLASHES": False,
        "OPEN_API": True,
        "OPEN_API_JSON_URL": "/openapi.json",
        "OPEN_API_SWAGGER_URL": "/docs"
    }

    def __init__(self, import_name: str, app_name: str = "PyJolt API", version: str = "1.0", env_path: str = None):
        """
        Initialization of PyJolt application
        """
        super().__init__()
        self.app_name = app_name
        self.version = version

        if env_path is not None:
            self._load_env(env_path)
        self._root_path = get_app_root_path(import_name)
        # Dictionary which holds application configurations
        self._configs = {**self.DEFAULT_CONFIGS}
        self._static_files_path = [f"{self._root_path + self.get_conf('STATIC_DIR')}"]
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")
        logging.basicConfig(level=logging.INFO)
        self._base_logger = logging.getLogger(self.get_conf("LOGGER_NAME"))

        self._app = self._base_app
        self._middleware = []

        # A list of registered exception methods via exception_handler decorator
        self._registered_exception_handlers = {}

        # Render engine (jinja2) set to None. If configs are provided it is initialized
        self._extensions = {}
        self.render_engine = None
        self.global_context_methods: list[Callable] = []

        self._on_startup_methods: list[Callable] = []
        self._on_shutdown_methods: list[Callable] = []
        self._before_request_methods: list[Callable] = []
        self._after_request_methods: list[Callable] = []
        self.openapi_spec = {}

        self._dependency_injection_map: dict[str, Callable] = {}

        self.cli = argparse.ArgumentParser(description="PyJolt CLI")
        self.subparsers = self.cli.add_subparsers(dest="command", help="CLI commands")
        self.cli_commands = {}

    def configure_app(self, configs: object|dict):
        """
        Configures application with provided configuration class or dictionary
        """
        if isinstance(configs, dict):
            self._configure_from_dict(configs)
        if isinstance(configs, object):
            self._configure_from_class(configs)

        # Sets new variables after configuring with object|dict
        self._static_files_path = [f"{self._root_path + self.get_conf('STATIC_DIR')}"]
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")
        self._base_logger = logging.getLogger(self.get_conf("LOGGER_NAME"))
        self.router.url_map.strict_slashes = self.get_conf("STRICT_SLASHES")


    def _initialize_jinja2(self):
        """
        Initializes jinja2 template render engine
        """
        self.render_engine = Environment(
            loader=FileSystemLoader(self._templates_path),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined if self._configs.get("TEMPLATES_STRICT", True) else Undefined
        )

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

    def _load_env(self, env_path: str):
        """
        Loads environment variables from <name>.env file
        """
        load_dotenv(dotenv_path=env_path, verbose=True)

    def add_cli_command(self, command_name: str, handler):
        """
        Adds a CLI command to the PyJolt CLI.
        """
        if command_name in self.cli_commands:
            raise ValueError(f"CLI command '{command_name}' is already registered.")
        self.cli_commands[command_name] = handler
        self.subparsers.add_parser(command_name, help=f"Run '{command_name}' command")

    def run_cli(self):
        """
        Executes the registered CLI commands.
        """
        args = self.cli.parse_args()
        if hasattr(args, "func"):
            args.func(args)  # pass the parsed arguments object
        else:
            self.cli.print_help()

    def use_middleware(self, middleware_factory):
        """
        Add a middleware factory to the stack.
        """
        self._middleware.append(middleware_factory)

    def add_extension(self, extension):
        """
        Adds extension to extension map
        """
        ext_name: str = extension.__name__ if hasattr(extension, "__name__") else extension.__class__.__name__
        self._extensions[ext_name] = extension

    def register_blueprint(self, bp: Blueprint, url_prefix=""):
        """
        Registers the blueprint, merging its routes into the app.
        """
        # Iterate over Rules in Blueprint and create a new Rule
        # to add it to the main app
        for rule in bp.router.url_map.iter_rules():
            # New Rule with Blueprints url prefix
            prefixed_rule = Rule(
                url_prefix + bp.url_prefix + rule.rule,
                endpoint=f"{bp.blueprint_name}.{rule.endpoint}",
                methods=rule.methods
            )
            # Adds new Rule to apps url map
            self.router.url_map.add(prefixed_rule)

        # Iterates over endpoints (names/functions) and adds them to the
        # main app with the Blueprints prefix
        for endpoint_name, func in bp.router.endpoints.items():
            namespaced_key = f"{bp.blueprint_name}.{endpoint_name}"
            self.router.endpoints[namespaced_key] = func
        
        if bp.static_folder_path is not None:
            self._static_files_path.append(bp.static_folder_path)
        
                # Iterates over all websocket rules of the blueprint
        for rule in bp.websockets_router.url_map.iter_rules():
            prefixed_rule = Rule(
                url_prefix + bp.url_prefix + rule.rule,
                endpoint=f"{bp.blueprint_name}.{rule.endpoint}",
                methods=rule.methods
            )
            self.websockets_router.url_map.add(prefixed_rule)
        
        # Iterates over websocket endpoints (names/functions) and adds them to the
        # main app with the Blueprints prefix
        for endpoint_name, func in bp.websockets_router.endpoints.items():
            namespaced_key = f"{bp.blueprint_name}.{endpoint_name}"
            self.websockets_router.endpoints[namespaced_key] = func

        self._merge_openapi_registry(bp)
        bp.add_app(self)

    def url_for(self, endpoint: str, **values) -> str:
        """
        Returns url for endpoint method
        :param endpoint: the name of the endpoint handler method namespaced 
        with the blueprint name (if in blueprint)
        :param values: dynamic route parameters
        :return: url (string) for endpoint
        """
        adapter = self.router.url_map.bind("")  # Binds map to base url
        #If a value starts with a forward slash, systems like MacOS/Linux treat it as an absolute path
        #maybe better if they are stripped of leading slashes?
        #values = {key: value.lstrip("/") for key, value in values.items()}
        try:
            return adapter.build(endpoint, values)
        except NotFound as exc:
            raise ValueError(f"Endpoint '{endpoint}' does not exist.") from exc
        except MethodNotAllowed as exc:
            raise ValueError(f"Endpoint '{endpoint}' exists but does not allow the method.") from exc
        except Exception as exc:
            raise ValueError(f"Error building URL for endpoint '{endpoint}': {exc}") from exc

    def exception_handler(self, exception: Exception):
        """
        Decorator for registering exception handler methods. THe
        decorated method gets the request and response object + any
        path variables passed to it
        """
        def decorator(func: Callable):
            self._add_exception_handler(func, exception)
            return func
        return decorator

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

    @property
    def on_startup(self):
        """
        Decorator for registering methods that should run before application
        starts. Methods are executed in the order they are appended to the list
        and get the application object passed as the only argument
        """
        def decorator(func: Callable):
            self.add_on_startup_method(func)
            return func
        return decorator

    @property
    def on_shutdown(self):
        """
        Decorator for registering methods that should run after application
        starts. Methods are executed in the order they are appended to the list
        and get the application object passed as the only argument
        """
        def decorator(func: Callable):
            self.add_on_shutdown_method(func)
            return func
        return decorator

    def _add_exception_handler(self, handler: Callable, exception: Exception):
        """
        Adds exception handler method to handler dictionary
        """
        handler_name: str = exception.__name__
        if handler_name in self._registered_exception_handlers:
            raise DuplicateExceptionHandler(f"Duplicate exception handler name {handler_name}")
        self._registered_exception_handlers[handler_name] = handler

    async def abort_route_not_found(self, send):
        """
        Aborts request because route was not found
        """
        # 404 - endpoint not found error
        await send({
            'type': 'http.response.start',
            'status': 404,
            'headers': [(b'content-type', b'application/json')]
        })
        await send({
            'type': 'http.response.body',
            'body': b'{ "status": "error", "message": "Endpoint not found" }'
        })

    async def send_response(self, res: Response, send):
        """
        Sends response
        """
        # Build headers for ASGI send
        headers = []
        for k, v in res.headers.items():
            headers.append((k.encode("utf-8"), v.encode("utf-8")))

        if not isinstance(res.body, bytes):
            res.body = json.dumps(res.body).encode()

        await send({
            "type": "http.response.start",
            "status": res.status_code,
            "headers": headers
        })

        await send({
            "type": "http.response.body",
            "body": res.body
        })

    def _log_request(self, scope, method: str, path: str) -> None:
        """
        Logs incoming request
        """
        self._base_logger.info(
            "HTTP request. CLIENT: %s, SCHEME: %s, METHOD: %s, PATH: %s, QUERY_STRING: %s",
            scope["client"][0],
            scope["scheme"],
            method,
            path,
            scope["query_string"].decode("utf-8")
        )

    def dependency_injection_map(self, injectable_name: str) -> Callable|None:
        """
        Returns the dependency injection map
        """
        return self._dependency_injection_map.get(injectable_name, None)

    def add_dependency_injection_to_map(self, injectable: Type, method: Callable):
        """
        Adds dependency injection method to dependency injection map 
        of application
        """
        self._dependency_injection_map[injectable.__name__] = method

    async def _base_app(self, req: Request, res: Response, send):
        """
        The bare-bones application without any middleware.
        """
        try:
            res = await run_sync_or_async(req.route_handler, req, res, **req.route_parameters)
        except (StaticAssetNotFound, SchemaValidationError, PydanticSchemaValidationError,
                MissingRequestData, AuthenticationException, InvalidJWTError, AborterException) as exc:
            res = res.json({
                "status": exc.status,
                "message": exc.message,
                "data": exc.data
            }).status(exc.status_code)
            #pylint: disable-next=W0718
        except Exception as exc:
            if exc.__class__.__name__ in self._registered_exception_handlers:
                res = await self._registered_exception_handlers[exc.__class__.__name__](req,
                                                                            res,
                                                                            exc)
            else:
                raise
        if res is None:
            raise MissingResponseObject()
        return await self.send_response(res, send)

    def build(self) -> None:
        """
        Build the final app by wrapping self._app in all middleware.
        Apply them in reverse order so the first middleware in the list
        is the outermost layer.
        """
        self._initialize_jinja2() #reinitilizes jinja2
        self._add_route_function("GET", f"{self.get_conf("STATIC_URL")}/<path:path>", static)
        if(self.get_conf("OPEN_API")):
            self.generate_openapi_spec()
            self._add_route_function("GET", self.get_conf("OPEN_API_JSON_URL"), open_api_json_spec)
            self._add_route_function("GET", self.get_conf("OPEN_API_SWAGGER_URL"), open_api_swagger)
        app = self._app
        for factory in reversed(self._middleware):
            app = factory(self, app)
        self._app = app

    async def _lifespan_app(self, scope, receive, send):
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

    async def _handle_websocket(self, scope, receive, send):
        """
        Handles incoming WebSocket connections using Werkzeug routing.
        """
        method: str = scope["type"]
        path: str = scope["path"]
        self._log_request(scope, method, path)
        websocket_handler, path_kwargs = self.websockets_router.match(path, method)
        if not websocket_handler:
            await send({"type": "websocket.close", "code": 1000})
            return

        async def websocket_receive():
            while True:
                message = await receive()
                if message["type"] == "websocket.receive":
                    yield message["text"]
                elif message["type"] == "websocket.disconnect":
                    break

        async def websocket_send(data: str):
            await send({"type": "websocket.send", "text": data})

        # Accept the WebSocket connection
        await send({"type": "websocket.accept"})

        try:
            await websocket_handler(websocket_receive, websocket_send, **path_kwargs)
        # pylint: disable-next=W0718
        except Exception as exc:
            self._base_logger.error("WebSocket error at %s: %s", path, exc)
        finally:
            try:
                await send({"type": "websocket.close", "code": 1000})
            except RuntimeError:
                self._base_logger.info("WebSocket already closed.")

    async def _handle_http_request(self, scope, receive, send):
        """
        Handles http requests
        """
        # We have a matching route
        method: str = scope["method"]
        path: str = scope["path"]
        self._log_request(scope, method, path)

        route_handler, path_kwargs = self.router.match(path, method)
        if not route_handler:
            return await self.abort_route_not_found(send)
        req = Request(scope, receive, self, path_kwargs, route_handler)
        res = Response(self, req, self.render_engine)
        return await self._app(req, res, send)

    async def __call__(self, scope, receive, send):
        """
        Once built, __call__ just delegates to the fully wrapped app.
        """
        if scope["type"] == "lifespan":
            return await self._lifespan_app(scope, receive, send)
        elif scope["type"] == "websocket":
            await self._handle_websocket(scope, receive, send)
        elif scope["type"] == "http":
            #await self._app(scope, receive, send)
            await self._handle_http_request(scope, receive, send)
        else:
            raise ValueError(f"Unsupported scope type {scope['type']}")

    def run(self, import_string=None, host="localhost", port=8080, reload=True,
            factory: bool = False, lifespan: str = "on", **kwargs) -> None:
        """
        Method for running the application. Should only be used for development.
        Starts a uvicorn server with the application instance.
        """
        # pylint: disable-next=C0415
        import uvicorn
        if not reload:
            return uvicorn.run(self, host=host, port=port,
                               factory=factory, lifespan=lifespan, **kwargs)
        if not import_string:
            raise ValueError(
                "If using the 'reload' option in the run method of the PyJolt application instance "
                "you must specify the application instance with an import string. Example: main:app"
            )
        uvicorn.run(import_string, host=host, port=port, log_level="info",
                    reload=reload, factory=factory, lifespan=lifespan, **kwargs)

    def get_conf(self, config_name: str, default: any = None) -> Any:
        """
        Returns app configuration with provided config_name.
        Raises error if configuration is not found.
        """
        if config_name in self.configs:
            return self.configs[config_name]
        return default

    def get_extension(self, ext_name: str|object):
        """
        Returns an extension by string name or object.__class__.__name__ property
        """
        if not isinstance(ext_name, str):
            ext_name = ext_name.__name__ if ext_name.__name__ else ext_name.__class__.__name__
        if ext_name not in self.extensions:
            raise MissingExtension(ext_name)
        return self.extensions[ext_name]

    def add_global_context_method(self, func: Callable):
        """
        Adds global context method to global_context_methods array
        """
        self.global_context_methods.append(func)

    def add_static_files_path(self, full_path: str):
        """
        Adds path to list of static files paths
        """
        self._static_files_path.append(full_path)

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
    def configs(self) -> dict[str, Any]:
        """
        Returns configuration dictionary
        """
        return self._configs

    @property
    def routing_table(self):
        """
        For debug/inspection: returns the underlying routing rules.
        """
        # If you want to inspect the final Map and endpoints:
        return {
            "rules": [str(rule) for rule in self.router.url_map.iter_rules()],
            "endpoints": list(self.router.endpoints.keys())
        }

    @property
    def static_files_path(self):
        """
        static files path
        """
        return self._static_files_path

    @property
    def templates_path(self):
        """
        templates directory path
        """
        return self._templates_path

    @property
    def extensions(self):
        """
        returns extension dictionary
        """
        return self._extensions

    @property
    def app(self):
        """
        Returns self
        For compatibility with the Blueprint class
        which contains the app object on the app property
        """
        return self
