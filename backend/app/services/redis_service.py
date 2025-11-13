"""
Redis client service for OAuth state storage, rate limiting, and caching.
"""

import redis
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get the global Redis client instance."""
    return _redis_client


def init_redis() -> Optional[redis.Redis]:
    """
    Initialize Redis connection.

    Returns Redis client on success, None on failure.
    In development, Redis is optional (falls back to in-memory).
    """
    global _redis_client

    redis_url = settings.effective_redis_url
    if not redis_url or redis_url == "redis://localhost:6379":
        if settings.is_production:
            raise ValueError("REDIS_URL must be set in production")
        logger.warning("No Redis URL configured; using in-memory fallback (dev only)")
        return None

    try:
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        _redis_client.ping()
        logger.info("Redis connection established")
        return _redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        if settings.is_production:
            raise
        logger.warning("Falling back to in-memory storage (dev only)")
        _redis_client = None
        return None


def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")
