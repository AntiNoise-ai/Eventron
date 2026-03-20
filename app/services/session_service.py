"""Chat session management — Redis-backed user session cache.

Replaces the in-memory _user_sessions dict that was in webhook.py.
Survives process restarts and works across multiple workers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# Session TTL: 24 hours (one event day)
SESSION_TTL_SECONDS = 86400

# Redis key prefix
_PREFIX = "eventron:session:"


class SessionService:
    """Redis-backed user session store.

    Stores {profile, event_id} keyed by IM user_id.
    """

    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client

    async def get(self, user_id: str) -> dict[str, Any] | None:
        """Load session for a user. Returns None if not found or expired."""
        raw = await self._redis.get(f"{_PREFIX}{user_id}")
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def save(self, user_id: str, session: dict[str, Any]) -> None:
        """Save session with TTL auto-refresh."""
        await self._redis.set(
            f"{_PREFIX}{user_id}",
            json.dumps(session, ensure_ascii=False),
            ex=SESSION_TTL_SECONDS,
        )

    async def delete(self, user_id: str) -> None:
        """Clear a user's session."""
        await self._redis.delete(f"{_PREFIX}{user_id}")


# ── Module-level Redis client (lazy init) ─────────────────────

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Get or create the shared Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


def get_session_service() -> SessionService:
    """Factory for SessionService — used by DI and webhook."""
    return SessionService(get_redis_client())
