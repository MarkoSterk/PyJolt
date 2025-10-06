"""
PyJolt application class
"""

# mypy: check-untyped-defs = True
import inspect
import argparse
import json
import asyncio
from typing import Any, Callable, Mapping, Optional, Type, TypeVar, cast
import aiofiles
from loguru import logger
from werkzeug.exceptions import NotFound, MethodNotAllowed
from pydantic import BaseModel, ValidationError

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
    StrictUndefined,
    Undefined,
)

from .exceptions.http_exceptions import HtmlAborterException, AborterException
from .http_statuses import HttpStatus
from .request import Request
from .response import Response
from .utilities import get_app_root_path, run_sync_or_async, import_module
from .exceptions import BaseHttpException, CustomException
from .router import Router
from .static import Static
from .open_api import OpenAPIController
from .controller import path

from .controller import Controller
from .exceptions import ExceptionHandler
from .base_extension import BaseExtension
from .configuration_base import BaseConfig
from .database.base_protocol import BaseModel as BaseModelClass
from .cli import CLIController

# ──────────────────────────────────────────────────────────────────────────────
# Monkey‐patch Uvicorn’s RequestResponseCycle.run_asgi so that, just before
# it invokes your ASGI app, it injects the real socket into the scope dict.
try:
    from uvicorn.protocols.http.h11_impl import RequestResponseCycle

    _orig_run_asgi = RequestResponseCycle.run_asgi

    async def _patched_run_asgi(self, application):
        # grab the raw socket from the transport and stash it into scope
        sock = None
        if hasattr(self, "transport") and self.transport is not None:
            sock = self.transport.get_extra_info("socket")
        if sock is not None:
            self.scope["socket"] = sock

        # now call the real ASGI loop
        return await _orig_run_asgi(self, application)

    RequestResponseCycle.run_asgi = _patched_run_asgi
# pylint: disable-next=W0718
except Exception as e:
    logger.debug(
        "Could not patch RequestResponseCycle.run_asgi; "
        "os.sendfile() zero-copy will fall back to aiofiles. "
        f"Patch error: {e}"
    )
# ──────────────────────────────────────────────────────────────────────────────


PYJOLT_ASCIART: str = r"""
  _______     __  _  ____  _   _______ 
 |  __ \ \   / / | |/ __ \| | |__   __|
 | |__) \ \_/ /  | | |  | | |    | |   
 |  ___/ \   /   | | |  | | |    | |   
 | |      | | |__| | |__| | |____| |   
 |_|      |_|\____/ \____/|______|_|   
A Fast, Simple, and Productive Python Web Framework
"""

T = TypeVar("T", bound="PyJolt")

def app_path(url_path: Optional[str] = None) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, "_base_url_path", url_path)
        return cls

    return decorator


def app(import_name: str, configs: Type[BaseConfig]) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, "_app_configs", {"import_name": import_name, "configs": configs})
        return cls

    return decorator


def on_startup(func) -> Callable:
    """
    Decorated methods will run in alphabetical order on app startup
    """
    setattr(func, "_on_startup_method", True)
    return func


def on_shutdown(func) -> Callable:
    """
    Decorated methods will run in alphabetical order on app shutdown
    """
    setattr(func, "_on_shutdown_method", True)
    return func


class MissingAppConfigurations(Exception):
    def __init__(
        self,
        msg: str = ("Missing application configurations. "
                    "Please make sure to use the @app_configs "
                    "decorator with appropriate arguments.")
    ):
        super().__init__(msg)


class MissingImportModule(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class WrongModuleLoadType(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


def validate_config(config_obj_or_type: Type[BaseConfig]) -> BaseConfig:
    # If it's already an instance
    if isinstance(config_obj_or_type, BaseConfig):
        return config_obj_or_type  # already validated by Pydantic

    if inspect.isclass(config_obj_or_type) and issubclass(
        config_obj_or_type, BaseConfig
    ):
        try:
            instance = config_obj_or_type()
        except Exception as e:
            raise MissingAppConfigurations(
                f"Could not instantiate config class {config_obj_or_type.__name__}: {e}"
            ) from e
        return BaseConfig.model_validate(instance.model_dump())

    raise MissingAppConfigurations("Configs must be a subclass of pyjolt.BaseConfig.")


class PyJolt:
    """PyJolt class implementation. Used to create a new application instance"""

    def __init__(self):
        """Init function"""
        app_configs: dict[str, str | object | dict] | None = getattr(
            self.__class__, "_app_configs", None
        )
        if app_configs is None:
            raise MissingAppConfigurations()

        import_name: str = cast(str, app_configs.get("import_name", None))
        configs: Type[BaseConfig] = cast(
            Type[BaseConfig], app_configs.get("configs", None)
        )
        if configs is None or not issubclass(configs, BaseConfig):
            raise MissingAppConfigurations(
                "Missing valid configs object in @app_configs. Configuration class must inherit from pyjolt.BaseConfig"
            )

        self._app_base_url: str = getattr(self.__class__, "_base_url_path", "")
        self._is_built = False
        self._root_path = get_app_root_path(import_name)
        # Dictionary which holds application configurations
        validated_configs: BaseConfig = validate_config(configs)
        self._configs = {**validated_configs.model_dump()}
        self._static_files_path = f"{self._root_path + self.get_conf('STATIC_DIR')}"
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")

        #creates Jinja2 environment for entire app
        self._jinja_environment = Environment(
            loader=FileSystemLoader(self._templates_path),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined
            if self.get_conf("TEMPLATES_STRICT", True)
            else Undefined,
            auto_reload=self.get_conf("DEBUG", False),
            enable_async=True,
        )

        self._router = Router(self.get_conf("STRICT_SLASHES", False))
        self._logger = logger

        self._app = self._base_app
        self._middleware: list[Callable] = []
        self._controllers: dict[str, "Controller"] = {}
        self._cli_controllers: dict[str, "CLIController"] = {}
        self._exception_handlers: dict[str, Callable] = {}
        self._json_spec: Optional[dict] = None
        self._db_models: dict[str, list[BaseModelClass]] = {}

        self._extensions: dict = {}
        self.global_context_methods: list[Callable] = []

        self._on_startup_methods: list[Callable] = []
        self._on_shutdown_methods: list[Callable] = []

        self._get_startup_methods()
        self._get_shutdown_methods()

        self.cli = argparse.ArgumentParser(description="PyJolt CLI")
        self.subparsers = self.cli.add_subparsers(dest="command", help="CLI commands")
        self.cli_commands: dict = {}

        models: Optional[list[str]] = self.get_conf("MODELS", None)
        controllers: Optional[list[str]] = self.get_conf("CONTROLLERS", None)
        cli_controllers: Optional[list[str]] = self.get_conf("CLI_CONTROLLERS", None)
        exception_handlers: Optional[list[str]] = self.get_conf(
            "EXCEPTION_HANDLERS", None
        )
        extensions: Optional[list[str]] = self.get_conf("EXTENSIONS", None)
        self._load_modules(models)
        self._load_modules(extensions)
        self._load_modules(controllers)
        self._load_modules(cli_controllers)
        self._load_modules(exception_handlers)

    def _load_modules(self, modules: Optional[list[str]] = None):
        if modules is None:
            return
        for import_string in modules:
            obj = import_module(import_string)
            if obj is None:
                raise MissingImportModule(
                    f"Failed to load module: {import_string}. Check path in configurations."
                )
            if inspect.isclass(obj) and issubclass(obj, Controller):
                self.logger.info(f"Registering controller: {obj.__name__}")
                self.register_controller(obj)
                continue
            if inspect.isclass(obj) and issubclass(obj, ExceptionHandler):
                self.logger.info(f"Registering exception handler: {obj.__name__}")
                self.register_exception_handler(obj)
                continue
            if isinstance(obj, BaseExtension):
                self.logger.info(f"Initilizing extension: {obj.__class__.__name__}")
                obj.init_app(self)
                continue
            if inspect.isclass(obj) and issubclass(obj, BaseModelClass):
                self.logger.info(f"Loaded database model: {obj.__name__}")
                if obj.db_name() not in self._db_models:
                    self._db_models[obj.db_name()] = []
                self._db_models[obj.db_name()].append(cast(BaseModelClass, obj))
                continue
            if inspect.isclass(obj) and issubclass(obj, CLIController):
                self.logger.info(f"Registering cli controller: {obj.__name__}")
                commands = getattr(obj, "_cli_command", {})
                cli_controller = obj(self, commands)
                self._cli_controllers[obj.__name__] = cli_controller
                continue
            raise WrongModuleLoadType(
                f"Failed to load module {obj.__name__ or obj.__class__.__name__}."
            )

    def _get_startup_methods(self):
        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            is_startup = getattr(method, "_on_startup_method", False)
            if is_startup:
                self._on_startup_methods.append(method)

    def _get_shutdown_methods(self):
        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            is_shutdown = getattr(method, "_on_shutdown_method", False)
            if is_shutdown:
                self._on_shutdown_methods.append(method)

    def get_conf(self, config_name: str, default: Any = None) -> Any:
        """
        Returns app configuration with provided config_name.
        Raises error if configuration is not found.
        """
        return self.configs.get(config_name, default)

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
            except HtmlAborterException as exc:
                res = (await req.res.html(exc.template, context=exc.data)).status(
                    exc.status_code
                )
                return await self.send_response(res, send, None)
            # pylint: disable-next=W0718
            except Exception as exc:
                handler = (
                    self._exception_handlers.get(exc.__class__.__name__, None) or None
                )
                if not handler:
                    raise Exception("Unhandled exception occured") from exc
                res = await run_sync_or_async(handler, req, exc)
                response_type = res.expected_body_type() or exc.__class__
                return await self.send_response(res, send, response_type)
        # pylint: disable-next=W0718
        except Exception as exc:
            # Catches every error and returns internal server error message
            # if the app is in production (DEBUG = False)
            # else reraises the error
            if not self.get_conf("DEBUG", False):
                res = req.res.json(
                    {
                        "status": "error",
                        "message": "Internal server error",
                    }
                ).status(HttpStatus.INTERNAL_SERVER_ERROR)
                self.logger.critical(f"Unhandled critical error: ({req.method}) {req.path}, {req.route_parameters}")
                return await self.send_response(res, send, Exception)
            raise

    async def abort_route_not_found(self, send, req: Request, path_data: Mapping[str, Any]):
        """
        Aborts request because route was not found
        """
        exc: NotFound|MethodNotAllowed|None = path_data.get("exc")
        if exc is not None:
            handler: Callable|None = (
                self._exception_handlers.get(exc.__class__.__name__, None) or None
            )
            if handler:
                res = await run_sync_or_async(handler, req, exc)
                response_type = res.expected_body_type() or exc.__class__
                return await self.send_response(res, send, response_type)
        ##sends generic response if custom handler not available
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

    async def send_response(
        self, res: Response, send, response_type: Optional[Type[Any]] = None
    ):
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
                "status": res.status_code.value
                if isinstance(res.status_code, HttpStatus)
                else res.status_code,
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
        if (
            response_type
            and issubclass(
                response_type, (CustomException, BaseHttpException, Exception)
            )
            and not issubclass(response_type, HtmlAborterException)
        ):
            res.body = json.dumps(res.body).encode("utf-8")
        elif (
            response_type
            and res.body
            and issubclass(response_type, BaseModel)
            and isinstance(res.body, dict)
        ):
            res.body = response_type(**res.body).model_dump_json().encode("utf-8")
        elif (
            response_type
            and res.body
            and issubclass(response_type, BaseModel)
            and isinstance(res.body, BaseModel)
        ):
            res.body = res.body.model_dump_json().encode("utf-8")
        elif res.body and response_type is None and isinstance(res.body, BaseModel):
            res.body = res.body.model_dump_json().encode("utf-8")
        elif res.body and not isinstance(res.body, (bytes, bytearray)):
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
                    await run_sync_or_async(method)

                # Signal uvicorn that startup is complete
                await send({"type": "lifespan.startup.complete"})

            elif message["type"] == "lifespan.shutdown":
                # Run your after_start methods (often used for cleanup)
                for method in self._on_shutdown_methods:
                    await run_sync_or_async(method)

                # Signal uvicorn that shutdown is complete
                await send({"type": "lifespan.shutdown.complete"})
                return  # Exit the lifespan loop

    async def _handle_http_request(self, scope, receive, send):
        """
        Handles http requests with CORS support (refactored)
        """
        method: str = scope["method"].upper()
        url_path: str = scope["path"]
        self._log_request(scope, method, url_path)

        route_handler, path_kwargs = self.router.match(url_path, method)
        req = Request(scope, receive, self, path_kwargs, cast(Callable, route_handler))

        if not route_handler:
            return await self.abort_route_not_found(send, req, path_kwargs)

        # CORS handling
        cors_opts = self._resolve_cors_options(cast(Callable, route_handler))
        origin = self._get_header(scope, "origin")
        is_preflight = (method == "OPTIONS") and bool(self._get_header(scope, "access-control-request-method"))

        if cors_opts["enabled"] and origin:
            if not self._origin_allowed(origin, cors_opts["allow_origins"]):
                return await self._cors_forbidden(send)

            if is_preflight:
                return await self._handle_preflight(scope, send, origin, cors_opts)

            # Wrap send to inject CORS headers on normal responses
            send = self._wrap_cors_send(send, origin, cors_opts)

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
        self.register_controller(static_controller)  # type: ignore

    def register_openapi_controller(self):
        openapi_controller_dec = path(
            self.get_conf("OPEN_API_URL"), open_api_spec=False
        )
        openapi_controller = openapi_controller_dec(OpenAPIController)
        self.register_controller(openapi_controller)

    def build(self) -> None:
        """
        Build the final app by wrapping self._app in all middleware.
        Apply them in reverse order so the first middleware in the list
        is the outermost layer.
        """
        print(PYJOLT_ASCIART)
        print(f"Starting PyJolt {self.version} application '{self.app_name}'")
        self.register_static_controller(self.get_conf("STATIC_URL"))
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

    def activate_extension(self, extension: "Type[BaseExtension]"):
        extension_instance = extension()
        extension_instance.init_app(self)

    def _add_route_function(
        self, method: str, url_path: str, func: Callable, endpoint_name: str
    ):
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
            ctrl_instance = ctrl(
                self, ctrl_path, ctrl_open_api_spec, ctrl_open_api_tags
            )

            self._controllers[ctrl_instance.path] = ctrl_instance
            endpoint_methods: dict[str, dict[str, str | Callable]] = (
                ctrl_instance.get_endpoint_methods()
            )
            for http_method, endpoints in endpoint_methods.items():
                for url_path, method in endpoints.items():
                    method_name: Callable = method["method"].__name__  # type: ignore
                    # handler: Callable = getattr(ctrl_instance, method_name) # type: ignore
                    endpoint_name: str = (
                        f"{ctrl_instance.__class__.__name__}.{method_name}"
                    )
                    self._add_route_function(
                        http_method,
                        self._app_base_url + ctrl_instance.path + url_path,
                        method["method"],
                        endpoint_name,
                    )

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

        self._json_spec = build_openapi(
            self._controllers,
            title=self.app_name,
            version=self.version,
            openapi_version="3.0.3",
            servers=["http://localhost:8080"],
        )

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
            func_args = args._get_args()
            func_kwargs = {name: value for name, value in args._get_kwargs() if name not in ["command", "func"]}
            asyncio.run(args.func(*func_args, **func_kwargs))  # pass the parsed arguments object
        else:
            self.cli.print_help()

    @property
    def json_spec(self) -> dict | None:
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
    def logger(self):
        return self._logger
    
    @property
    def jinja_environment(self) -> Environment:
        return self._jinja_environment

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
    
    # ───────────────────────── CORS utilities ─────────────────────────

    def _get_header(self, scope, name: str) -> Optional[str]:
        target = name.lower().encode("latin1")
        for k, v in scope.get("headers", []):
            if k.lower() == target:
                try:
                    return v.decode("latin1")
                except Exception:
                    return None
        return None

    def _normalize_list(self, v, *, upper: bool = False) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        out = [s.strip() for s in v if s and s.strip()]
        if upper:
            out = [s.upper() for s in out]
        return out

    def _global_cors_options(self) -> dict[str, Any]:
        return {
            "enabled": self.get_conf("CORS_ENABLED"),
            "allow_origins": self.get_conf("CORS_ALLOW_ORIGINS"),
            "allow_methods": self.get_conf("CORS_ALLOW_METHODS"),
            "allow_headers": self.get_conf("CORS_ALLOW_HEADERS"),
            "expose_headers": self.get_conf("CORS_EXPOSE_HEADERS"),
            "allow_credentials": self.get_conf("CORS_ALLOW_CREDENTIALS"),
            "max_age": self.get_conf("CORS_MAX_AGE"),
        }

    def _resolve_cors_options(self, handler: Optional[Callable]) -> dict[str, Any]:
        """
        Merge global and endpoint-level CORS options.
        If handler has @no_cors, CORS is completely disabled.
        """
        opts = self._global_cors_options()

        if handler is None:
            return opts

        # Check if handler explicitly disables CORS
        if getattr(handler, "_disable_cors", False):
            opts["enabled"] = False
            return opts

        # Merge @cors decorator overrides
        overrides = getattr(handler, "_cors_options", None) or {}
        for k, v in overrides.items():
            if v is not None:
                opts[k] = v

        opts["allow_origins"] = self._normalize_list(opts["allow_origins"])
        opts["allow_methods"] = self._normalize_list(opts["allow_methods"], upper=True)
        opts["allow_headers"] = self._normalize_list(opts["allow_headers"])
        opts["expose_headers"] = self._normalize_list(opts["expose_headers"])
        return opts

    def _origin_allowed(self, origin: Optional[str], allow_origins: list[str]) -> bool:
        if not origin:
            return True
        if "*" in allow_origins:
            return True
        return origin in allow_origins

    def _build_cors_headers_for_preflight(
        self,
        *,
        origin: str,
        request_method: Optional[str],
        request_headers: Optional[str],
        opts: dict[str, Any]
    ) -> list[tuple[bytes, bytes]]:
        allow_methods = opts["allow_methods"]
        allow_headers = opts["allow_headers"]

        # echo requested headers if none configured
        if not allow_headers and request_headers:
            allow_headers = [h.strip() for h in request_headers.split(",") if h.strip()]

        # If "*" configured but credentials allowed: echo back the Origin
        allow_origin_value = "*"
        if opts["allow_credentials"] or ("*" not in opts["allow_origins"]):
            allow_origin_value = origin

        headers: list[tuple[bytes, bytes]] = [
            (b"access-control-allow-origin", allow_origin_value.encode("latin1")),
            (b"vary", b"Origin"),
            (b"access-control-allow-methods", ", ".join(allow_methods).encode("latin1")),
            (b"access-control-allow-headers", ", ".join(allow_headers).encode("latin1")),
        ]
        if opts["allow_credentials"]:
            headers.append((b"access-control-allow-credentials", b"true"))
        if opts.get("max_age") is not None:
            headers.append((b"access-control-max-age", str(int(opts["max_age"])).encode("latin1")))
        return headers

    def _build_cors_headers_for_response(
        self,
        *,
        origin: Optional[str],
        opts: dict[str, Any]
    ) -> list[tuple[bytes, bytes]]:
        if not origin:
            return []

        # If "*" configured but credentials allowed: echo Origin instead.
        allow_origin_value = "*"
        if opts["allow_credentials"] or ("*" not in opts["allow_origins"]):
            allow_origin_value = origin

        headers: list[tuple[bytes, bytes]] = [
            (b"access-control-allow-origin", allow_origin_value.encode("latin1")),
            (b"vary", b"Origin"),
        ]
        if opts["allow_credentials"]:
            headers.append((b"access-control-allow-credentials", b"true"))
        expose = opts.get("expose_headers") or []
        if expose:
            headers.append((b"access-control-expose-headers", ", ".join(expose).encode("latin1")))
        return headers
    
    async def _cors_forbidden(self, send):
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"status":"error","message":"CORS origin not allowed"}',
        })

    async def _method_not_allowed(self, send, message: bytes = b"Preflight method not allowed"):
        await send({
            "type": "http.response.start",
            "status": 405,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        })
        await send({
            "type": "http.response.body",
            "body": message,
        })

    async def _handle_preflight(self, scope, send, origin: str, cors_opts: dict):
        acr_method = self._get_header(scope, "access-control-request-method")
        acr_headers = self._get_header(scope, "access-control-request-headers")

        if acr_method and cors_opts["allow_methods"] and acr_method.upper() not in cors_opts["allow_methods"]:
            return await self._method_not_allowed(send)

        headers = self._build_cors_headers_for_preflight(
            origin=origin,
            request_method=acr_method,
            request_headers=acr_headers,
            opts=cors_opts,
        )
        await send({
            "type": "http.response.start",
            "status": 204,  # No Content
            "headers": headers,
        })
        await send({"type": "http.response.body", "body": b""})

    def _wrap_cors_send(self, send, origin: str, cors_opts: dict):
        cors_headers = self._build_cors_headers_for_response(origin=origin, opts=cors_opts)
        async def cors_send(event):
            if event.get("type") == "http.response.start":
                headers = event.get("headers", [])
                event = {**event, "headers": headers + cors_headers}
            await send(event)
        return cors_send
