"""
In-memory cache implementation
"""
from typing import Optional, cast, TYPE_CHECKING
import asyncio

from cachetools import TTLCache

from .base_cache_backend import BaseCacheBackend

if TYPE_CHECKING:
    from ...pyjolt import PyJolt

class MemoryCacheBackend(BaseCacheBackend):
    """
    In-memory cache using cachetools.TTLCache for bounded size and base TTL.


    We honor per-item TTL by storing an explicit expire timestamp alongside
    the payload; TTLCache provides a global upper bound and eviction.
    """

    def __init__(self, default_ttl: int = 300, maxsize: int = 10_000):
        self.default_ttl = int(default_ttl)
        # Stores: key -> {payload: dict, expire: float}
        self._cache: TTLCache[str, dict] = TTLCache(maxsize=maxsize, ttl=self.default_ttl)

    # ---- config ----
    @classmethod
    def configure_from_app(cls, app: "PyJolt", variable_prefix: str) -> "MemoryCacheBackend":
        default_ttl = int(app.get_conf(f"{variable_prefix}CACHE_DURATION", 300))
        maxsize = int(app.get_conf(f"{variable_prefix}CACHE_MEMORY_MAXSIZE", 10_000))
        return cls(default_ttl=default_ttl, maxsize=maxsize)

    async def connect(self) -> None: # pragma: no cover - nothing to do
        return None

    async def disconnect(self) -> None:
        self._cache.clear()

    async def get(self, key: str) -> Optional[dict]:
        item = self._cache.get(key)
        if not item:
            return None
        expire = item.get("expire", 0)
        if expire < asyncio.get_event_loop().time():
            try:
                del self._cache[key]
            except KeyError:
                pass
            return None
        return cast(dict, item.get("payload"))

    async def set(self, key: str, value: dict, duration: Optional[int] = None) -> None:
        ttl = int(duration) if duration is not None else self.default_ttl
        expire = asyncio.get_event_loop().time() + ttl
        self._cache[key] = {"payload": value, "expire": expire}

    async def delete(self, key: str) -> None:
        try:
            del self._cache[key]
        except KeyError:
            pass

    async def clear(self) -> None:
        self._cache.clear()
