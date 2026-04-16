"""Redis client initialization and dependency injection.

Provides async Redis connection pool for caching, pub/sub messaging,
and session management across backend services.
"""

import os

import redis.asyncio as redis

from config import settings

redis_client = redis.from_url(os.getenv("REDIS_URL", settings.REDIS_URL))


async def get_redis_client():
    """Return the async Redis client instance for dependency injection.

    Returns:
        Configured redis.asyncio.Redis client connected to REDIS_URL.
    """
    return redis_client
