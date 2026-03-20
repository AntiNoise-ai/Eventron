"""Authentication service — JWT token management + password hashing.

No direct DB access — uses OrganizerRepository.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.models.organizer import Organizer
from app.repositories.organizer_repo import OrganizerRepository
from app.services.exceptions import (
    AuthenticationError,
    DuplicateEmailError,
)

logger = logging.getLogger(__name__)

# JWT config
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# ── Password hashing (stdlib only, no bcrypt dep) ────────────

def _hash_password(password: str) -> str:
    """Hash password with PBKDF2-SHA256 + random salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, hash_hex = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ── JWT helpers ──────────────────────────────────────────────

def create_access_token(organizer_id: uuid.UUID) -> str:
    """Create a JWT access token for an organizer."""
    payload = {
        "sub": str(organizer_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises on invalid/expired."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ── Service class ────────────────────────────────────────────

class AuthService:
    """Business logic for organizer authentication."""

    def __init__(self, organizer_repo: OrganizerRepository):
        self._repo = organizer_repo

    async def register(
        self,
        email: str,
        password: str,
        name: str,
        phone: str | None = None,
    ) -> Organizer:
        """Register a new organizer account."""
        if await self._repo.email_exists(email):
            raise DuplicateEmailError(f"Email {email} is already registered")

        password_hash = _hash_password(password)
        return await self._repo.create(
            email=email,
            password_hash=password_hash,
            name=name,
            phone=phone,
            role="admin",  # first user is admin; future: invite system
        )

    async def login(self, email: str, password: str) -> tuple[Organizer, str]:
        """Authenticate and return (organizer, access_token).

        Raises AuthenticationError on invalid credentials.
        """
        organizer = await self._repo.get_by_email(email)
        if organizer is None:
            raise AuthenticationError("Invalid email or password")

        if not organizer.is_active:
            raise AuthenticationError("Account is disabled")

        if not _verify_password(password, organizer.password_hash):
            raise AuthenticationError("Invalid email or password")

        token = create_access_token(organizer.id)
        return organizer, token

    async def get_current_organizer(self, organizer_id: uuid.UUID) -> Organizer:
        """Look up organizer by ID (from decoded JWT)."""
        org = await self._repo.get_by_id(organizer_id)
        if org is None or not org.is_active:
            raise AuthenticationError("Invalid or disabled account")
        return org
