"""
redis_client — Shared Redis connection factory with in-process fallback.

When REDIS_URL points to an unreachable server (e.g. no Docker in a demo
environment), the factory silently falls back to fakeredis — a fully
compatible in-process Redis implementation.

All API modules import `get_redis_client()` instead of building their own
`redis.Redis.from_url()` calls, so the fallback is applied consistently.

Usage::

    from app.services.redis_client import get_redis_client
    r = get_redis_client()
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import redis

logger = logging.getLogger("BobaMaster.RedisClient")

# Module-level singleton — created once, reused on every call
_client: Optional[redis.Redis] = None
_using_fallback: bool = False

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_redis_client() -> redis.Redis:
    """
    Return a Redis client, creating it on first call.

    Attempts to connect to REDIS_URL.  If the connection is refused or
    times out, falls back to an in-process fakeredis instance so all agents
    continue to work without a running Redis server.

    The fallback is stateful for the lifetime of the process — all API
    modules share the same in-memory store.
    """
    global _client, _using_fallback

    if _client is not None:
        return _client

    # ── Try real Redis first ──────────────────────────────────────────
    try:
        real = redis.Redis.from_url(REDIS_URL, decode_responses=False,
                                    socket_connect_timeout=2,
                                    socket_timeout=2)
        real.ping()   # raises if unreachable
        _client = real
        logger.info(f"Connected to Redis at {REDIS_URL}")
        return _client
    except Exception as exc:
        logger.warning(
            f"Redis unavailable ({exc}). "
            "Falling back to in-process fakeredis — data is ephemeral and "
            "resets on server restart. Start Redis for persistence."
        )

    # ── Fall back to fakeredis ────────────────────────────────────────
    try:
        import fakeredis
        _client = fakeredis.FakeRedis(decode_responses=False)
        _using_fallback = True
        logger.info("fakeredis in-process store is active.")
        return _client
    except ImportError:
        raise RuntimeError(
            "Redis is unreachable and fakeredis is not installed. "
            "Run `pip install fakeredis` or start Redis with Docker."
        )


def is_using_fallback() -> bool:
    """True if the process is running on in-memory fakeredis, not real Redis."""
    get_redis_client()   # ensure initialised
    return _using_fallback
