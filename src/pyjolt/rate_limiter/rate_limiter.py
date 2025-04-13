"""
ratelimit.py
Module for rate limiting support (in-memory & Redis).
"""

import time
from typing import Optional, Callable
from redis.asyncio import Redis, from_url
from ..pyjolt import PyJolt
from ..utilities import run_sync_or_async

class RateLimiter:
    """
    Rate Limiting system for requests. Supports:
    - In-memory limiting (for development/testing/small-scale production).
    - Redis limiting (for large-scale apps).
    """

    def __init__(self, app: PyJolt = None):
        self._app: Optional[PyJolt] = None

        # Configuration variables
        self._use_redis = False
        self._redis_url = None
        self._redis_password = None
        self._redis_backend: Optional[Redis] = None
        self._limiter_error_message: str = "Too many requests."

        # Default rate-limiting settings
        self._limit = 100     # Maximum number of requests
        self._window = 60     # Time window in seconds
        # A simple dictionary to track usage when in-memory
        # Format: { key: (window_start_timestamp, count) }
        self._in_memory_store = {}

        if app:
            self.init_app(app)

    def init_app(self, app: PyJolt) -> None:
        """
        Initializes the rate limiting system with a PyJolt application.
        Reads configuration from the app and registers startup/shutdown hooks.
        """
        self._app = app
        self._redis_url = self._app.get_conf("RATE_LIMIT_REDIS_URL", self._redis_url)
        self._redis_password = self._app.get_conf("RATE_LIMIT_REDIS_PASSWORD", self._redis_password)
        self._limit = self._app.get_conf("RATE_LIMIT_MAX_REQUESTS", self._limit)
        self._window = self._app.get_conf("RATE_LIMIT_WINDOW_SECONDS", self._window)
        self._limiter_error_message = self._app.get_conf("RATE_LIMIT_ERROR_MESSAGE", self._limiter_error_message)

        if self._redis_url:
            self._use_redis = True

        # Register this extension and lifecycle methods
        self._app.add_extension(self)
        self._app.add_on_startup_method(self.connect)
        self._app.add_on_shutdown_method(self.disconnect)

    async def connect(self, _) -> None:
        """Create a Redis connection if Redis-based rate limiting is configured."""
        if self._use_redis and not self._redis_backend:
            self._redis_backend = await from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=False,
                password=self._redis_password
            )

    async def disconnect(self, _) -> None:
        """Close the Redis connection if open."""
        if self._redis_backend:
            await self._redis_backend.close()
            self._redis_backend = None
    
    @property
    def no_limit(self) -> Callable:
        """
        Assignes no rate limit to decorated handler
        """
        def decorator(func: Callable):
            setattr(func, "_limiter_no_limits", True)
            return func
        return decorator
    
    def set_rules(self, configs: dict[str, int]) -> Callable:
        """
        Decorator for setting special cors rules to endpoint
        Configs parameters
        :param window: int in seconds
        :param limit: int number of requests
        """
        def decorator(func: Callable):
            setattr(func, "_limiter_rules", configs)
            return func
        return decorator
    
    async def _return_limiter_response(self, send):
        # If limited, immediately send a 429 response
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"application/json"),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": f'{{"message": "{self._limiter_error_message}", "status": "error"}}'.encode("utf-8"),
        })

    def middleware(self, app: PyJolt, app_function: Callable):
        """
        Returns an ASGI middleware function that implements rate limiting.
        You can add this middleware to your `middleware_stack` or
        decorate your routes if your framework supports per-route middlewares.
        """

        async def rate_limit_middleware(req, res, send):
            # Only handle HTTP requests
            if req.scope["type"] != "http":
                return await self._app.app_function(req, res, send)

            if not getattr(req.route_handler, "_limiter_no_limits", False):

                route_rules: dict = getattr(req.route_handler, "_limiter_rules", {})

                client = req.scope.get("user", None) or req.scope.get("client", None) or "unknown"

                if isinstance(client, tuple):
                    # scope["client"] = (ip, port)
                    client = req.scope["client"][0]

                if not isinstance(client, str):
                    #Gets the signature from the user object
                    client = client.signature()

                #If route handler has special rules the route path/method is added to the key
                if len(route_rules.keys()) > 0:
                    client = f'{client}|{req.scope.get("method")}|{req.scope.get("path")}'
                is_limited = False

                if self._use_redis:
                    # Key could be "rl:<window_start_timestamp>:<client>"
                    # Alternatively, you can store the increment in a key for the current window
                    window_key = self._current_window_key(client)
                    is_limited = await self._handle_redis_limit(window_key, route_rules)
                else:
                    # In-memory approach
                    is_limited = self._handle_in_memory_limit(client, route_rules)

                if is_limited:
                    await self._return_limiter_response(send)
                    return

            # Otherwise, wrap the send so we can pass it along
            async def wrapped_send(event):
                await send(event)

            return await run_sync_or_async(app_function, req, res, wrapped_send)

        return rate_limit_middleware

    async def _handle_redis_limit(self, window_key: str, route_rules: dict) -> bool:
        """
        Increment usage in Redis and check if rate limit is exceeded.
        Using a simple fixed-window approach:
        - The `window_key` changes when the current time window changes.
        - We keep an expiry on the key equal to `self._window` seconds or 
        based on the route handler specific configs.
        """

        if not self._redis_backend:
            # If for some reason redis is not connected, fallback to in-memory
            return self._handle_in_memory_limit(window_key, route_rules)

        # Redis command sequence (pseudo-atomic with MULTI/EXEC or Lua script if needed).
        pipe = self._redis_backend.pipeline(transaction=True)
        pipe.incr(window_key)
        pipe.expire(window_key, route_rules.get("window", self._window))
        results = await pipe.execute()

        request_count = results[0]  # result of INCR
        if request_count > route_rules.get("limit", self._limit):
            return True  # Over the limit
        return False

    def _handle_in_memory_limit(self, client: str, route_rules: dict) -> bool:
        """
        In-memory approach to rate limit:
        - If the current time is still within the window, increment count.
        - Otherwise, start a new window and reset count.
        """

        current_time = time.time()
        key = self._current_window_key(client)

        # Check if we have an entry for this key
        if key not in self._in_memory_store:
            self._in_memory_store[key] = (current_time, 1)
            return False

        window_start, count = self._in_memory_store[key]

        # If we're still within the same window
        if current_time - window_start < route_rules.get("window", self._window):
            count += 1
            self._in_memory_store[key] = (window_start, count)
            if count > route_rules.get("limit", self._limit):
                return True
        else:
            # Start a new window
            self._in_memory_store[key] = (current_time, 1)

        return False

    def _current_window_key(self, client_identifier: str) -> str:
        """
        Generate a key for the current time window.
        """
        current_window_start = int(time.time() // self._window) * self._window
        return f"rl:{client_identifier}:{current_window_start}"

