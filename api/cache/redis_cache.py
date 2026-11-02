"""Redis caching implementation."""

import json
import hashlib
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta
import logging
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Redis client instance
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # Create mock redis client for fallback
        redis_client = MockRedis()
        logger.warning("Using mock Redis client as fallback")


def get_redis_client() -> Union[redis.Redis, 'MockRedis']:
    """Get Redis client instance."""
    global redis_client
    
    if redis_client is None:
        import asyncio
        asyncio.create_task(init_redis())
    
    return redis_client


def generate_cache_key(value_type: str, value: str, operation: str = "default") -> str:
    """Generate cache key from value type and value."""
    key_data = f"{value_type}:{value}:{operation}"
    return f"cybersec:{hashlib.md5(key_data.encode()).hexdigest()}"


async def cache_get(cache_key: str) -> Optional[Any]:
    """Get value from cache."""
    try:
        client = get_redis_client()
        
        # Handle mock redis
        if isinstance(client, MockRedis):
            return await client.get(cache_key)
        
        value = await client.get(cache_key)
        
        if value is None:
            return None
        
        # Try to deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
            
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"Redis cache get error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected cache get error: {e}")
        return None


async def cache_set(
    cache_key: str, 
    value: Any, 
    ttl: Optional[int] = None
) -> bool:
    """Set value in cache with optional TTL."""
    try:
        client = get_redis_client()
        
        # Use default TTL if not specified
        if ttl is None:
            ttl = settings.CACHE_TTL_DEFAULT
        
        # Serialize value to JSON
        try:
            serialized_value = json.dumps(value, default=str)
        except (TypeError, ValueError):
            serialized_value = str(value)
        
        # Handle mock redis
        if isinstance(client, MockRedis):
            return await client.set(cache_key, serialized_value, ttl)
        
        # Set with TTL
        await client.setex(cache_key, ttl, serialized_value)
        return True
        
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"Redis cache set error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected cache set error: {e}")
        return False


async def cache_delete(cache_key: str) -> bool:
    """Delete value from cache."""
    try:
        client = get_redis_client()
        
        # Handle mock redis
        if isinstance(client, MockRedis):
            return await client.delete(cache_key)
        
        result = await client.delete(cache_key)
        return bool(result)
        
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"Redis cache delete error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected cache delete error: {e}")
        return False


async def cache_exists(cache_key: str) -> bool:
    """Check if cache key exists."""
    try:
        client = get_redis_client()
        
        # Handle mock redis
        if isinstance(client, MockRedis):
            return await client.exists(cache_key)
        
        result = await client.exists(cache_key)
        return bool(result)
        
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"Redis cache exists error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected cache exists error: {e}")
        return False


async def cache_increment(cache_key: str, amount: int = 1) -> Optional[int]:
    """Increment cache counter."""
    try:
        client = get_redis_client()
        
        # Handle mock redis
        if isinstance(client, MockRedis):
            return await client.incr(cache_key, amount)
        
        result = await client.incrby(cache_key, amount)
        return result
        
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"Redis cache increment error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected cache increment error: {e}")
        return None


# Rate limiting cache functions
async def check_rate_limit(
    api_key: str, 
    endpoint: str,
    max_requests: int,
    window_seconds: int
) -> tuple[bool, int]:
    """
    Check if API key has exceeded rate limit.
    
    Returns:
        (is_allowed, remaining_requests)
    """
    try:
        client = get_redis_client()
        
        # Generate rate limit key
        now = datetime.utcnow()
        window_start = now.replace(second=0, microsecond=0)
        if window_seconds < 60:
            window_start = now.replace(minute=0, second=0, microsecond=0)
        
        rate_limit_key = f"rate_limit:{api_key}:{endpoint}:{window_start.isoformat()}"
        
        # Handle mock redis
        if isinstance(client, MockRedis):
            current_count = await client.incr(rate_limit_key)
            if current_count == 1:
                await client.expire(rate_limit_key, window_seconds)
            remaining = max(0, max_requests - current_count)
            is_allowed = current_count <= max_requests
            return is_allowed, remaining
        
        # Use Redis pipeline for atomic operations
        pipe = client.pipeline()
        pipe.incr(rate_limit_key)
        pipe.expire(rate_limit_key, window_seconds)
        results = await pipe.execute()
        
        current_count = results[0]
        remaining = max(0, max_requests - current_count)
        is_allowed = current_count <= max_requests
        
        return is_allowed, remaining
        
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        # On error, allow request but log warning
        return True, max_requests


# Caching decorators
def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Cache decorator for async functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(
                key_prefix or func.__name__,
                str(args) + str(kwargs),
                "cache"
            )
            
            # Try to get from cache
            cached_result = await cache_get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_set(cache_key, result, ttl)
                logger.debug(f"Cache set for {cache_key}")
            
            return result
        
        return wrapper
    return decorator


class MockRedis:
    """Mock Redis client for fallback when Redis is not available."""
    
    def __init__(self):
        self._data = {}
        self._ttl = {}
    
    async def ping(self) -> bool:
        return True
    
    async def get(self, key: str) -> Optional[str]:
        # Check if key exists and not expired
        if key in self._ttl and datetime.utcnow() > self._ttl[key]:
            del self._data[key]
            del self._ttl[key]
            return None
        return self._data.get(key)
    
    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self._data[key] = value
        self._ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
        return True
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        self._data[key] = value
        if ttl:
            self._ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
        if key in self._ttl:
            del self._ttl[key]
        return 1
    
    async def exists(self, key: str) -> int:
        if key in self._ttl and datetime.utcnow() > self._ttl[key]:
            del self._data[key]
            del self._ttl[key]
            return 0
        return 1 if key in self._data else 0
    
    async def incr(self, key: str, amount: int = 1) -> int:
        current_value = self._data.get(key, "0")
        try:
            new_value = int(current_value) + amount
        except ValueError:
            new_value = amount
        self._data[key] = str(new_value)
        return new_value
    
    async def expire(self, key: str, ttl: int) -> bool:
        self._ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
        return True
    
    async def close(self):
        pass


# Cache utilities
async def clear_cache_pattern(pattern: str) -> int:
    """Clear cache keys matching pattern."""
    try:
        client = get_redis_client()
        
        # Handle mock redis
        if isinstance(client, MockRedis):
            keys_to_delete = [k for k in self._data.keys() if pattern in k]
            for key in keys_to_delete:
                await cache_delete(key)
            return len(keys_to_delete)
        
        # Get all keys matching pattern
        keys = await client.keys(pattern)
        
        if keys:
            # Delete all matching keys
            await client.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache keys matching pattern: {pattern}")
        
        return len(keys)
        
    except Exception as e:
        logger.error(f"Error clearing cache pattern {pattern}: {e}")
        return 0


async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        client = get_redis_client()
        
        if isinstance(client, MockRedis):
            return {
                "total_keys": len(client._data),
                "memory_usage": "mock",
                "hit_rate": "mock"
            }
        
        # Get Redis info
        info = await client.info()
        
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "cache_hit_rate": 0.0
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}


# Health check
async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health."""
    try:
        client = get_redis_client()
        
        start_time = datetime.utcnow()
        await client.ping()
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "message": "Redis is responding"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }