"""
pyjolt main class
"""
import argparse
import logging
from typing import Any, Callable
from dotenv import load_dotenv

from werkzeug.routing import Rule
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined, Undefined

#from .exceptions import DuplicateRoutePath
from .common import Common
from .blueprint import Blueprint
from .request import Request
from .response import Response
from .router import Router
from .utilities import get_app_root_path
from .static import static
from .exceptions import (DuplicateExceptionHandler, MissingExtension,
                        StaticAssetNotFound, SchemaValidationError,
                        AuthenticationException)

class PyJolt(Common):
    """
    PyJolt ASGI server class, now using a Router for advanced path matching.
    """

    DEFAULT_CONFIGS: dict[str, any] = {
        "LOGGER_NAME": "PyJolt_logger",
        "TEMPLATES_DIR": "/templates",
        "STATIC_DIR": "/static",
        "TEMPLATES_STRICT": "TEMPLATES_STRICT",
        "DEFAULT_RESPONSE_DATA_FIELD": "data"
    }

    def __init__(self, import_name: str, env_path: str = ".env"):
        """
        Initialization of PyJolt application
        """
        self._root_path = get_app_root_path(import_name)
        # Dictionary which holds application configurations
        self._configs = {**self.DEFAULT_CONFIGS}
        self._static_files_path = self._root_path + self.get_conf("STATIC_DIR")
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")
        self._load_env(env_path)
        logging.basicConfig(level=logging.INFO)
        self._base_logger = logging.getLogger(self.get_conf("LOGGER_NAME"))

        # Our internal, bare-bones ASGI app
        self._app = self._base_app
        # A list to store middleware factories
        self._middleware = []

        # A list of registered exception methods via exception_handler decorator
        self._registered_exception_handlers = {}

        # Render engine (jinja2) set to None. If configs are provided it is initialized
        self._extensions = {}
        self.render_engine = None
        self.router = Router()
        self._add_route_function("GET", "/static/<path:path_name>", static)
        self._before_start_methods = []
        self._after_start_methods = []

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
        self._static_files_path = self._root_path + self.get_conf("STATIC_DIR")
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")
        self._base_logger = logging.getLogger(self.get_conf("LOGGER_NAME"))


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

    def before_start(self):
        """
        Decorator for registering methods that should run before application
        starts. Methods are executed in the order they are appended to the list
        and get the application object passed as the only argument
        """
        def decorator(func: Callable):
            self._before_start_methods.append(func)
            return func
        return decorator

    def after_start(self):
        """
        Decorator for registering methods that should run after application
        starts. Methods are executed in the order they are appended to the list
        and get the application object passed as the only argument
        """
        def decorator(func: Callable):
            self._after_start_methods.append(func)
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

    async def _base_app(self, scope, receive, send):
        """
        The bare-bones application without any middleware.
        """
        if scope['type'] == 'http':
            method: str = scope["method"]
            path: str = scope["path"]
            self._log_request(scope, method, path)

            route_handler, path_kwargs = self.router.match(path, method)
            if not route_handler:
                return await self.abort_route_not_found(send)

            # We have a matching route
            req = Request(scope, receive, self)
            res = Response(self.render_engine)
            try:
                await route_handler(req, res, **path_kwargs)
            except (StaticAssetNotFound, SchemaValidationError, AuthenticationException) as exc:
                res.json({
                    "status": exc.status,
                    "message": exc.message,
                    "data": exc.data
                }, exc.status_code)
                #pylint: disable-next=W0718
            except Exception as exc:
                if exc.__class__.__name__ in self._registered_exception_handlers:
                    await self._registered_exception_handlers[exc.__class__.__name__](req,
                                                                                res,
                                                                                exc,
                                                                                **path_kwargs)
                else:
                    raise
            return await self.send_response(res, send)

    def build(self) -> None:
        """
        Build the final app by wrapping self._app in all middleware.
        Apply them in reverse order so the first middleware in the list
        is the outermost layer.
        """
        self._initialize_jinja2() #reinitilizes jinja2
        app = self._app
        for factory in reversed(self._middleware):
            app = factory(self, app)
        self._app = app

    async def __call__(self, scope, receive, send):
        """
        Once built, __call__ just delegates to the fully wrapped app.
        """
        for method in self._before_start_methods:
            await method(self)
        await self._app(scope, receive, send)
        for method in self._after_start_methods:
            await method(self)

    def run(self, import_string=None, host="localhost", port=8080, reload=True, **kwargs) -> None:
        """
        Method for running the application. Should only be used for development.
        Starts a uvicorn server with the application instance.
        """
        # pylint: disable-next=C0415
        import uvicorn
        if not reload:
            return uvicorn.run(self, host=host, port=port, **kwargs)
        if not import_string:
            raise ValueError(
                "If using the 'reload' option in the run method of the PyJolt application instance "
                "you must specify the application instance with an import string. Example: main:app"
            )
        uvicorn.run(import_string, host=host, port=port, log_level="info", reload=reload, **kwargs)

    def get_conf(self, config_name: str, default: any = None) -> Any:
        """
        Returns app configuration with provided config_name.
        Raises error if configuration is not found.
        """
        if config_name in self.configs:
            return self.configs[config_name]
        if default is not None:
            return default
        raise ValueError(f"Configuration property with name {config_name} is not defined")

    def get_extension(self, ext_name: str|object):
        """
        Returns an extension by string name or object.__class__.__name__ property
        """
        if not isinstance(ext_name, str):
            ext_name = ext_name.__name__ if ext_name.__name__ else ext_name.__class__.__name__
        if ext_name not in self.extensions:
            raise MissingExtension(ext_name)
        return self.extensions[ext_name]

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
