"""
Multi-tier caching layer.
Primary: Redis (if configured)
Fallback: In-process TTLCache
"""
import pickle
from typing import Any, Optional

from cachetools import TTLCache
from loguru import logger

from config import get_settings

settings = get_settings()


def _serialize(value: Any) -> bytes:
    return pickle.dumps(value)


def _deserialize(data: bytes) -> Any:
    return pickle.loads(data)


class InMemoryCache:
    """Thread-safe in-memory TTL cache using cachetools."""

    def __init__(self):
        # key -> (value, expiry_ts)
        self._stores: dict[str, TTLCache] = {}

    def _get_store(self, ttl: int) -> TTLCache:
        key = str(ttl)
        if key not in self._stores:
            self._stores[key] = TTLCache(maxsize=2000, ttl=ttl)
        return self._stores[key]

    def get(self, key: str, ttl: int = 30) -> Optional[Any]:
        store = self._get_store(ttl)
        return store.get(key)

    def set(self, key: str, value: Any, ttl: int = 30):
        store = self._get_store(ttl)
        store[key] = value

    def delete(self, key: str):
        for store in self._stores.values():
            store.pop(key, None)

    def clear(self):
        for store in self._stores.values():
            store.clear()


class RedisCache:
    """Redis-backed async cache."""

    def __init__(self, url: str):
        self._url = url
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                from redis import asyncio as redis_async

                self._redis = redis_async.from_url(self._url, decode_responses=False)
            except Exception as e:
                logger.warning(f"[Redis] Connection failed: {e}")
                raise
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        try:
            r = await self._get_redis()
            data = await r.get(key)
            if data is None:
                return None
            return _deserialize(data)
        except Exception as e:
            logger.debug(f"[Redis] Get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 30):
        try:
            r = await self._get_redis()
            await r.setex(key, ttl, _serialize(value))
        except Exception as e:
            logger.debug(f"[Redis] Set failed for {key}: {e}")

    async def delete(self, key: str):
        try:
            r = await self._get_redis()
            await r.delete(key)
        except Exception:
            pass


class CacheManager:
    """
    Unified cache manager with automatic fallback from Redis to in-memory.
    All get/set operations are synchronous (in-memory) since Redis is optional.
    Use get_async/set_async for Redis-aware async operations.
    """

    def __init__(self):
        self._memory = InMemoryCache()
        self._redis: Optional[RedisCache] = None
        self._redis_available = False

        if settings.USE_REDIS:
            self._redis = RedisCache(settings.REDIS_URL)

    def get(self, key: str, ttl: int = 30) -> Optional[Any]:
        """Synchronous get from in-memory cache."""
        return self._memory.get(key, ttl)

    def set(self, key: str, value: Any, ttl: int = 30):
        """Synchronous set to in-memory cache."""
        self._memory.set(key, value, ttl)

    async def get_async(self, key: str, ttl: int = 30) -> Optional[Any]:
        """Try Redis first, fall back to memory."""
        if self._redis and self._redis_available:
            val = await self._redis.get(key)
            if val is not None:
                return val
        return self._memory.get(key, ttl)

    async def set_async(self, key: str, value: Any, ttl: int = 30):
        """Write to both Redis and memory."""
        self._memory.set(key, value, ttl)
        if self._redis and self._redis_available:
            await self._redis.set(key, value, ttl)

    async def init_redis(self):
        """Attempt to initialize Redis connection."""
        if not self._redis:
            return
        try:
            r = await self._redis._get_redis()
            await r.ping()
            self._redis_available = True
            logger.info("[Cache] Redis connected successfully")
        except Exception as e:
            logger.warning(f"[Cache] Redis unavailable, using in-memory: {e}")
            self._redis_available = False


# Global singleton
cache_manager = CacheManager()
