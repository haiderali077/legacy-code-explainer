"""
Redis-backed rate limiting using a sliding-window counter pattern.
Falls back to in-memory dict when Redis is unavailable (development only).
"""

import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

_redis_client = None
_fallback_store: dict = defaultdict(list)


def init_rate_limiter(redis_client) -> None:
    """Initialize rate limiter with Redis client."""
    global _redis_client
    _redis_client = redis_client
    logger.info("Rate limiter initialized with Redis backend")


async def check_rate_limit(
    request: Request,
    limit: int = 60,
    window_seconds: int = 60,
    key_prefix: str = "rl",
) -> None:
    """
    Check rate limit for the incoming request.

    Raises HTTPException 429 if rate limit exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"{key_prefix}:{client_ip}"
    now = time.time()

    if _redis_client:
        try:
            pipe = _redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds)
            results = pipe.execute()
            request_count = results[2]
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}; allowing request")
            return
    else:
        # Fallback: in-memory (for local dev)
        _fallback_store[key] = [
            ts for ts in _fallback_store[key] if ts > now - window_seconds
        ]
        _fallback_store[key].append(now)
        request_count = len(_fallback_store[key])

    if request_count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(window_seconds)},
        )


def rate_limit(limit: int = 60, window_seconds: int = 60):
    """
    FastAPI dependency for rate limiting.

    Usage:
        @router.get("/endpoint", dependencies=[Depends(rate_limit(30, 60))])
        async def my_endpoint(): ...
    """
    async def _dependency(request: Request):
        await check_rate_limit(request, limit=limit, window_seconds=window_seconds)
    return _dependency
