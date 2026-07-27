"""
Production Redis Connection Manager & Caching Layer.

Provides async Redis client wrapper with fallback in-memory caching
for development/testing environments.
"""
import json
import logging
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger("app.core.redis")

_in_memory_cache: dict = {}


class RedisCacheManager:

    def __init__(self):
        self.redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._is_connected = False

    async def connect(self) -> None:
        """Initialize connection to Redis server."""
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            await self._client.ping()
            self._is_connected = True
            logger.info("Connected to Redis server successfully.")
        except Exception as e:
            logger.warning(f"Redis connection unavailable ({e}). Falling back to in-memory cache.")
            self._is_connected = False

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        if self._is_connected and self._client:
            try:
                val = await self._client.get(key)
                return json.loads(val) if val else None
            except Exception:
                pass
        val = _in_memory_cache.get(key)
        return json.loads(val) if val else None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set cached value with TTL."""
        val_str = json.dumps(value)
        if self._is_connected and self._client:
            try:
                await self._client.set(key, val_str, ex=ttl_seconds)
                return True
            except Exception:
                pass
        _in_memory_cache[key] = val_str
        return True

    async def delete(self, key: str) -> bool:
        """Delete cached key."""
        if self._is_connected and self._client:
            try:
                await self._client.delete(key)
            except Exception:
                pass
        _in_memory_cache.pop(key, None)
        return True

    async def flush(self) -> None:
        """Clear cache."""
        if self._is_connected and self._client:
            try:
                await self._client.flushdb()
            except Exception:
                pass
        _in_memory_cache.clear()


redis_cache = RedisCacheManager()
