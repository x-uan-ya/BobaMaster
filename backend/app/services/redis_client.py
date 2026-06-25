"""
redis_client — Shared Redis factory with pure-Python in-memory fallback.

redis-py 5+ sends the HELLO command on every connection. fakeredis 2.x
does not implement HELLO, causing an immediate crash when no real Redis
server is available.

This module solves the incompatibility by providing a hand-written
InMemoryRedis class that implements exactly the commands used by
InventoryService and ContextAgent — no fakeredis, no sockets, no HELLO.

Priority order
──────────────
1. Connect to real Redis (REDIS_URL env var, 2-second timeout).
2. Fall back to InMemoryRedis — stateful for the process lifetime.
"""

from __future__ import annotations

import logging
import os
import time
from threading import Lock
from typing import Any, Optional, Union

import redis

logger = logging.getLogger("BobaMaster.RedisClient")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: Optional[Any] = None          # redis.Redis or InMemoryRedis
_using_fallback: bool = False
_lock = Lock()


# ─────────────────────────────────────────────────────────────────────────────
# Pure-Python in-memory store
# ─────────────────────────────────────────────────────────────────────────────

class InMemoryRedis:
    """
    Thread-safe drop-in replacement for the redis.Redis interface.

    Implements every command used by InventoryService and ContextAgent:
      Strings : get, set, setex, delete, exists
      Hashes  : hset, hgetall
      Sorted  : zadd, zrange, zrangebyscore, zrem, zscore
      Pipeline: pipeline (returns a simple Pipeline proxy)
    """

    def __init__(self) -> None:
        self._strings:  dict[str, tuple[bytes, Optional[float]]] = {}  # key -> (value, expire_at|None)
        self._hashes:   dict[str, dict[bytes, bytes]] = {}
        self._zsets:    dict[str, dict[bytes, float]] = {}
        self._lock = Lock()

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _enc(v: Any) -> bytes:
        if isinstance(v, bytes):  return v
        if isinstance(v, str):    return v.encode()
        return str(v).encode()

    def _is_expired(self, key: str) -> bool:
        entry = self._strings.get(key)
        if entry is None:          return False
        _, exp = entry
        if exp is None:            return False
        return time.time() > exp

    def _clean(self, key: str) -> None:
        if self._is_expired(key):
            del self._strings[key]

    # ── Strings ───────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            self._clean(key)
            entry = self._strings.get(key)
            return entry[0] if entry else None

    def set(self, key: str, value: Any) -> bool:
        with self._lock:
            self._strings[key] = (self._enc(value), None)
            return True

    def setex(self, key: str, ttl_seconds: int, value: Any) -> bool:
        with self._lock:
            exp = time.time() + ttl_seconds
            self._strings[key] = (self._enc(value), exp)
            return True

    def delete(self, *keys: str) -> int:
        with self._lock:
            count = 0
            for key in keys:
                for store in (self._strings, self._hashes, self._zsets):
                    if key in store:
                        del store[key]
                        count += 1
                        break
            return count

    def exists(self, key: str) -> int:
        with self._lock:
            self._clean(key)
            return int(
                key in self._strings
                or key in self._hashes
                or key in self._zsets
            )

    # ── Hashes ────────────────────────────────────────────────────────

    def hset(self, key: str, field: Any = None, value: Any = None,
             mapping: Optional[dict] = None) -> int:
        with self._lock:
            h = self._hashes.setdefault(key, {})
            count = 0
            if mapping:
                for f, v in mapping.items():
                    h[self._enc(f)] = self._enc(v)
                    count += 1
            elif field is not None:
                h[self._enc(field)] = self._enc(value)
                count = 1
            return count

    def hgetall(self, key: str) -> dict[bytes, bytes]:
        with self._lock:
            return dict(self._hashes.get(key, {}))

    # ── Sorted sets ───────────────────────────────────────────────────

    def zadd(self, key: str, mapping: dict[Any, float]) -> int:
        with self._lock:
            z = self._zsets.setdefault(key, {})
            added = 0
            for member, score in mapping.items():
                bm = self._enc(member)
                if bm not in z:
                    added += 1
                z[bm] = float(score)
            return added

    def zrangebyscore(self, key: str, min_score: Any, max_score: Any) -> list[bytes]:
        with self._lock:
            z = self._zsets.get(key, {})
            lo = float("-inf") if min_score in ("-inf", b"-inf") else float(min_score)
            hi = float("+inf") if max_score in ("+inf", b"+inf") else float(max_score)
            return [m for m, s in sorted(z.items(), key=lambda x: x[1]) if lo <= s <= hi]

    def zrange(self, key: str, start: int, stop: int) -> list[bytes]:
        with self._lock:
            z = self._zsets.get(key, {})
            items = sorted(z.items(), key=lambda x: x[1])
            if stop == -1:
                sliced = items[start:]
            else:
                sliced = items[start:stop + 1]
            return [m for m, _ in sliced]

    def zrem(self, key: str, *members: Any) -> int:
        with self._lock:
            z = self._zsets.get(key, {})
            removed = 0
            for m in members:
                bm = self._enc(m)
                if bm in z:
                    del z[bm]
                    removed += 1
            return removed

    def zscore(self, key: str, member: Any) -> Optional[float]:
        with self._lock:
            z = self._zsets.get(key, {})
            return z.get(self._enc(member))

    def ping(self) -> bool:
        return True

    # ── Pipeline ──────────────────────────────────────────────────────

    def pipeline(self, transaction: bool = True) -> "_Pipeline":
        return _Pipeline(self)


class _Pipeline:
    """Minimal pipeline proxy — queues calls, executes them atomically."""

    def __init__(self, r: InMemoryRedis) -> None:
        self._r = r
        self._queue: list[tuple] = []

    def __getattr__(self, name: str):
        def _record(*args, **kwargs):
            self._queue.append((name, args, kwargs))
            return self
        return _record

    def execute(self) -> list:
        results = []
        for name, args, kwargs in self._queue:
            results.append(getattr(self._r, name)(*args, **kwargs))
        self._queue.clear()
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Public factory
# ─────────────────────────────────────────────────────────────────────────────

def get_redis_client() -> Any:
    """
    Return a working Redis client (singleton).

    Tries real Redis first (2-second timeout). Falls back to InMemoryRedis
    if the server is unreachable — no external packages needed.
    """
    global _client, _using_fallback

    if _client is not None:
        return _client

    with _lock:
        if _client is not None:   # double-checked locking
            return _client

        try:
            real: redis.Redis = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            real.ping()
            _client = real
            logger.info(f"Redis connected: {REDIS_URL}")
            return _client
        except Exception as exc:
            logger.warning(
                f"Redis unavailable ({type(exc).__name__}: {exc}). "
                "Using in-process InMemoryRedis — state resets on restart."
            )

        _client = InMemoryRedis()
        _using_fallback = True
        logger.info("InMemoryRedis active (no Redis server required).")
        return _client


def is_using_fallback() -> bool:
    """True when running on the in-memory store instead of real Redis."""
    get_redis_client()
    return _using_fallback
