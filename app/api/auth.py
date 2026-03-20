"""Auth API routes — organizer login, register, profile."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.deps import get_auth_service
from app.schemas.auth import (
    LoginRequest,
    OrganizerResponse,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService, decode_access_token
from app.services.exceptions import AuthenticationError, DuplicateEmailError

router = APIRouter()
_bearer = HTTPBearer()


# ── Dependency: extract current organizer from JWT ───────────

async def get_current_organizer(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    svc: AuthService = Depends(get_auth_service),
):
    """FastAPI dependency that validates JWT and returns Organizer."""
    try:
        payload = decode_access_token(credentials.credentials)
        organizer_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        return await svc.get_current_organizer(organizer_id)
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or disabled account")


# ── Routes ───────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    svc: AuthService = Depends(get_auth_service),
):
    """Register a new organizer account."""
    try:
        organizer = await svc.register(
            email=body.email,
            password=body.password,
            name=body.name,
            phone=body.phone,
        )
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Email already registered")

    _, token = await svc.login(body.email, body.password)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    svc: AuthService = Depends(get_auth_service),
):
    """Authenticate and get access token."""
    try:
        _, token = await svc.login(body.email, body.password)
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=OrganizerResponse)
async def get_me(organizer=Depends(get_current_organizer)):
    """Get current organizer profile."""
    return OrganizerResponse.model_validate(organizer)
