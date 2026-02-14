"""Unified cache adapter for async operations."""

import redis.asyncio as redis
import json
from typing import Optional, Any, List
from datetime import timedelta


class CacheAdapter:
    """Async cache adapter with Redis backend."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: timedelta = timedelta(hours=1)
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Establish connection to Redis."""
        if self._connected:
            return
        
        self._client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self._client.ping()
        self._connected = True
    
    async def disconnect(self) -> None:
        """Close connection to Redis."""
        if self._client:
            await self._client.close()
            self._connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._connected:
            await self.connect()
        
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set value in cache."""
        if not self._connected:
            await self.connect()
        
        try:
            serialized = json.dumps(value)
            if ttl:
                await self._client.setex(
                    key,
                    int(ttl.total_seconds()),
                    serialized
                )
            else:
                await self._client.set(key, serialized)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._connected:
            await self.connect()
        
        try:
            await self._client.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            await self.connect()
        
        try:
            return await self._client.exists(key) > 0
        except Exception:
            return False
    
    async def get_many(self, keys: List[str]) -> dict:
        """Get multiple values from cache."""
        if not self._connected:
            await self.connect()
        
        result = {}
        try:
            values = await self._client.mget(keys)
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
        except Exception:
            pass
        
        return result
    
    async def set_many(
        self,
        mapping: dict,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set multiple values in cache."""
        if not self._connected:
            await self.connect()
        
        try:
            pipe = self._client.pipeline()
            for key, value in mapping.items():
                serialized = json.dumps(value)
                if ttl:
                    pipe.setex(key, int(ttl.total_seconds()), serialized)
                else:
                    pipe.set(key, serialized)
            await pipe.execute()
            return True
        except Exception:
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._connected:
            await self.connect()
        
        keys = []
        try:
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self._client.delete(*keys)
        except Exception:
            pass
        
        return 0
    
    async def flush_db(self) -> bool:
        """Flush all keys from current database."""
        if not self._connected:
            await self.connect()
        
        try:
            await self._client.flushdb()
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self._connected:
            await self.connect()
        
        try:
            info = await self._client.info('stats')
            return {
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'connected_clients': info.get('connected_clients', 0),
            }
        except Exception:
            return {}
