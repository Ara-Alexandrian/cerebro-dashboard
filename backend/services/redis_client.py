"""
Redis client for Cerebro real-time state
"""
import os
from typing import Optional
import redis.asyncio as redis

# Connection instance
_redis: Optional[redis.Redis] = None

# Config from environment
REDIS_HOST = os.getenv("REDIS_HOST", "172.21.0.11")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))


async def init_redis():
    """Initialize Redis connection"""
    global _redis
    _redis = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )
    # Test connection
    await _redis.ping()


async def close_redis():
    """Close Redis connection"""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def get_redis() -> redis.Redis:
    """Get the Redis connection"""
    if not _redis:
        raise RuntimeError("Redis not initialized")
    return _redis


# Convenience methods for bot state
async def set_bot_state(bot_id: int, state: dict):
    """Set bot real-time state"""
    r = await get_redis()
    await r.hset(f"bot:{bot_id}", mapping=state)


async def get_bot_state(bot_id: int) -> dict:
    """Get bot real-time state"""
    r = await get_redis()
    return await r.hgetall(f"bot:{bot_id}")


async def publish_event(channel: str, message: str):
    """Publish event for real-time updates"""
    r = await get_redis()
    await r.publish(channel, message)
