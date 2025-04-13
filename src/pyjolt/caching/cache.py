"""
cache.py
Module for caching support (in-memory & Redis).
"""

import asyncio
import pickle
from functools import wraps
from typing import Optional, Callable, Any
from redis.asyncio import Redis, from_url
from ..pyjolt import PyJolt
from ..response import Response
from ..request import Request
from ..utilities import run_sync_or_async

class Cache:
    """
    Caching system for route handlers. Supports:
    - In-memory caching (for development/testing).
    - Redis caching (for production).
    - Decorator to cache route handler results.
    """

    def __init__(self, app: PyJolt = None):
        self._cache_backend: Optional[Redis] = None
        self._local_cache: dict = {}
        self._use_redis = False
        self._duration = 300  # Default cache time-to-live (5 minutes)
        self._redis_url = None
        self._redis_password = None
        self._app = None

        if app:
            self.init_app(app)

    def init_app(self, app: PyJolt) -> None:
        """
        Initializes the caching system. Supports Redis or local cache.
        """
        self._app = app
        self._redis_url = self._app.get_conf("CACHE_REDIS_URL", False)
        self._duration = self._app.get_conf("CACHE_DURATION", 300)
        self._redis_password = self._app.get_conf("CACHE_REDIS_PASSWORD", False)

        if self._redis_url:
            self._use_redis = True

        self._app.add_extension(self)
        self._app.add_on_startup_method(self.connect)
        self._app.add_on_shutdown_method(self.disconnect)

    async def connect(self, _) -> None:
        """
        Initializes Redis connection if enabled.
        """
        if self._use_redis and not self._cache_backend:
            self._cache_backend = await from_url(self._redis_url, encoding="utf-8", decode_responses=False, password=self._redis_password)

    async def disconnect(self, _) -> None:
        """
        Closes Redis connection.
        """
        if self._cache_backend:
            await self._cache_backend.close()
            self._cache_backend = None

    async def set(self, key: str, value: Any, duration: Optional[int] = None) -> None:
        """
        Stores a value in the cache.
        """
        duration = duration or self._duration
        #stores only the neccessary parts of the response
        value = {
            "status_code": value.status_code,
            "headers": value.headers,
            "body": value.body
        }
        if self._use_redis:
            await self._cache_backend.setex(key, duration, pickle.dumps(value))
        else:
            self._local_cache[key] = (value, asyncio.get_event_loop().time() + duration)
    
    async def make_cached_response(self, cached_data, req: Request) -> Response|None:
        """
        Creates response object with cached data
        """
        res: Response = Response(self._app, req)
        res.body = cached_data["body"]
        res.status_code = cached_data["status_code"]
        res.headers = cached_data["headers"]
        return res


    async def get(self, key: str, req: Request) -> Any:
        """
        Retrieves a value from the cache.
        """
        if self._use_redis:
            cached_data = await self._cache_backend.get(key)
            if cached_data:
                cached_data = pickle.loads(cached_data)
                return await self.make_cached_response(cached_data, req)
            return None

        if key in self._local_cache:
            cached_data, expiry = self._local_cache[key]
            if expiry > asyncio.get_event_loop().time():
                return await self.make_cached_response(cached_data, req)
            del self._local_cache[key]
        return None

    async def delete(self, key: str) -> None:
        """
        Deletes a value from the cache.
        """
        if self._use_redis:
            await self._cache_backend.delete(key)
        else:
            self._local_cache.pop(key, None)

    async def clear(self) -> None:
        """
        Clears all cache.
        """
        if self._use_redis:
            await self._cache_backend.flushdb()
        else:
            self._local_cache.clear()

    def cache(self, duration: int = None) -> Callable:
        """
        Decorator for caching route handler results.
        The decorator should be placed as the first decorator (bottom-most)
        on route functions. This way, the result of the route function is
        cached and not the result of other decorators. This is important
        especially when using authentication.
        Example:
        ```
        @app.get("/")
        @other_decorators
        @cache.cache(duration=120)
        async def get_data(req: Request, res: Response):
            return res.json({"data": "some_value"}).status(200)
        ```
        """

        def decorator(handler: Callable) -> Callable:
            @wraps(handler)
            async def wrapper(*args, **kwargs) -> Response:
                req: Request = args[0]
                method: str = req.method
                path: str = req.path
                query_params: dict = sorted(req.query_params.items())
                cache_key = f"{handler.__name__}:{method}:{path}:{hash(frozenset(query_params))}"
                cached_value = await self.get(cache_key, req)
                if cached_value is not None:
                    return cached_value  # Return cached response
                res: Response = await run_sync_or_async(handler, *args, **kwargs)
                await self.set(cache_key, res, duration)  # Cache the response
                return res

            return wrapper
        return decorator
