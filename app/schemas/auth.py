"""Pydantic schemas for auth API."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Email + password login."""

    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """New organizer registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class OrganizerResponse(BaseModel):
    """Organizer profile response."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    name: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
