"""
PyJolt application class
"""

import json
from typing import Any, Callable, Optional, TYPE_CHECKING
import aiofiles
from dotenv import load_dotenv
from loguru import logger

from .request import Request
from .response import Response
from .utilities import get_app_root_path, run_sync_or_async
from .exceptions import BaseHttpException, CustomException, MissingResponseObject
from .router import Router
from .static import static

if TYPE_CHECKING:
    from .controller import Controller

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
        "LOGGER_NAME": "PyJolt_logger",
        "TEMPLATES_DIR": "/templates",
        "STATIC_DIR": "/static",
        "STATIC_URL": "/static",
        "TEMPLATES_STRICT": "TEMPLATES_STRICT",
        "DEFAULT_RESPONSE_DATA_FIELD": "data",
        "STRICT_SLASHES": False,
        "OPEN_API": True,
        "OPEN_API_JSON_URL": "/openapi.json",
        "OPEN_API_SWAGGER_URL": "/docs",
    }

    def __init__(
        self,
        import_name: str,
        app_name: str = "PyJolt API",
        version: str = "1.0",
        env_path: Optional[str] = None,
    ):
        """Init function"""

        self.app_name = app_name
        self.version = version

        if env_path is not None:
            self._load_env(env_path)
        self._root_path = get_app_root_path(import_name)
        # Dictionary which holds application configurations
        self._configs = {**self.DEFAULT_CONFIGS}
        self._static_files_path = [f"{self._root_path + self.get_conf('STATIC_DIR')}"]
        self._templates_path = self._root_path + self.get_conf("TEMPLATES_DIR")
        self._router = Router(self.get_conf("STRICT_SLASHES", False))

        self._app = self._base_app
        self._middleware: list[Callable] = []
        self._controllers: dict[str, "Controller"] = {}

        self._registered_exception_handlers = {}

        self._extensions = {}
        self.global_context_methods: list[Callable] = []

        self._on_startup_methods: list[Callable] = []
        self._on_shutdown_methods: list[Callable] = []

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
        self._static_files_path = [f"{self._root_path + self.get_conf('STATIC_DIR')}"]
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

    def add_static_files_path(self, full_path: str):
        """
        Adds path to list of static files paths
        """
        self._static_files_path.append(full_path)

    async def _base_app(self, req: Request, send):
        """
        The bare-bones application without any middleware.
        """
        try:
            res: Response = await run_sync_or_async(
                req.route_handler, req, **req.route_parameters
            )
        except (CustomException, BaseHttpException) as exc:
            status = "error"
            message = "Internal server error"
            data = None
            status_code = 500
            if isinstance(exc, BaseHttpException):
                status = exc.status
                message = exc.message
                data = exc.data
                status_code = exc.status_code
            res = req.res.json(
                {"status": status, "message": message, "data": data}
            ).status(status_code)
            # pylint: disable-next=W0718
        except Exception as exc:
            if exc.__class__.__name__ in self._registered_exception_handlers:
                res: Response = await self._registered_exception_handlers[
                    exc.__class__.__name__
                ](req, exc)
            else:
                raise
        if res is None:
            raise MissingResponseObject()
        return await self.send_response(res, send)

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

    async def send_response(self, res: Response, send):
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
                "status": res.status_code,
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

        if res.body is not None and not isinstance(res.body, (bytes, bytearray)):
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
        path: str = scope["path"]
        self._log_request(scope, method, path)
        route_handler, path_kwargs = self.router.match(path, method)
        if not route_handler:
            return await self.abort_route_not_found(send)
        req = Request(scope, receive, self, path_kwargs, route_handler)
        return await self._app(req, send)

    def _log_request(self, scope, method: str, path: str) -> None:
        """
        Logs incoming request
        """
        logger.info(
            f"HTTP request. CLIENT: {scope['client'][0]}, SCHEME: {scope['scheme']}, METHOD: {method}, PATH: {path}, QUERY_STRING: {scope['query_string'].decode('utf-8')}"
        )

    def build(self) -> None:
        """
        Build the final app by wrapping self._app in all middleware.
        Apply them in reverse order so the first middleware in the list
        is the outermost layer.
        """
        self._add_route_function(
            "GET", f"{self.get_conf('STATIC_URL')}/<path:path>", static
        )
        app = self._base_app
        for factory in reversed(self._middleware):
            app = factory(self, app)
        self._app = app

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

    def register_controller(self, ctrl: "Controller"):
        """Registers controller class with application"""
        path: str = getattr(ctrl, "_controller_path")
        ctrl = ctrl(self, path);
        self._controllers[ctrl.path] = ctrl
        endpoint_methods: dict[str, dict[str, str|Callable]] = ctrl.get_endpoint_methods()
        for path, method in endpoint_methods.items():
            http_method: str = method["http_method"]
            endpoint: Callable = method["method"].__name__
            self._add_route_function(http_method, ctrl.path+path, getattr(ctrl, endpoint))

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

    async def __call__(self, scope, receive, send):
        """
        Once built, __call__ just delegates to the fully wrapped app.
        """
        if scope["type"] == "lifespan":
            return await self._lifespan_app(scope, receive, send)
        if scope["type"] == "http":
            # await self._app(scope, receive, send)
            return await self._handle_http_request(scope, receive, send)
        raise ValueError(f"Unsupported scope type {scope['type']}")
