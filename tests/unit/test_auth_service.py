"""Unit tests for AuthService — password hashing, JWT, registration."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.services.auth_service import (
    AuthService,
    _hash_password,
    _verify_password,
    create_access_token,
    decode_access_token,
)
from app.services.exceptions import AuthenticationError, DuplicateEmailError


# ── Password hashing ─────────────────────────────────────────

class TestPasswordHashing:
    """Password hash + verify round-trip."""

    def test_hash_and_verify_correct_password(self):
        hashed = _hash_password("mypassword123")
        assert _verify_password("mypassword123", hashed)

    def test_wrong_password_fails(self):
        hashed = _hash_password("correct")
        assert not _verify_password("wrong", hashed)

    def test_different_hashes_for_same_password(self):
        h1 = _hash_password("same")
        h2 = _hash_password("same")
        assert h1 != h2  # different salts

    def test_empty_password_works(self):
        hashed = _hash_password("")
        assert _verify_password("", hashed)

    def test_malformed_hash_returns_false(self):
        assert not _verify_password("password", "no-dollar-sign")

    def test_unicode_password(self):
        hashed = _hash_password("密码测试🔑")
        assert _verify_password("密码测试🔑", hashed)


# ── JWT tokens ───────────────────────────────────────────────

class TestJWT:
    """JWT create + decode round-trip."""

    def test_create_and_decode(self):
        uid = uuid.uuid4()
        token = create_access_token(uid)
        payload = decode_access_token(token)
        assert payload["sub"] == str(uid)

    def test_decode_invalid_token_raises(self):
        with pytest.raises(Exception):
            decode_access_token("garbage.token.here")

    def test_token_contains_exp(self):
        token = create_access_token(uuid.uuid4())
        payload = decode_access_token(token)
        assert "exp" in payload


# ── AuthService ──────────────────────────────────────────────

class TestAuthService:
    """AuthService with mocked repository."""

    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock()
        repo.email_exists.return_value = False
        repo.get_by_email.return_value = None
        return repo

    @pytest.fixture
    def svc(self, mock_repo):
        return AuthService(mock_repo)

    async def test_register_success(self, svc, mock_repo):
        mock_repo.create.return_value = AsyncMock(
            id=uuid.uuid4(), email="test@example.com", name="Test",
            is_active=True, role="admin"
        )
        result = await svc.register("test@example.com", "password123", "Test")
        mock_repo.create.assert_called_once()
        call_kwargs = mock_repo.create.call_args.kwargs
        assert call_kwargs["email"] == "test@example.com"
        assert "password_hash" in call_kwargs
        assert call_kwargs["password_hash"] != "password123"

    async def test_register_duplicate_email_raises(self, svc, mock_repo):
        mock_repo.email_exists.return_value = True
        with pytest.raises(DuplicateEmailError):
            await svc.register("taken@example.com", "password", "Name")

    async def test_login_success(self, svc, mock_repo):
        pw_hash = _hash_password("correct")
        mock_org = AsyncMock(
            id=uuid.uuid4(), email="user@test.com", password_hash=pw_hash,
            is_active=True
        )
        mock_repo.get_by_email.return_value = mock_org

        org, token = await svc.login("user@test.com", "correct")
        assert org == mock_org
        assert len(token) > 0

    async def test_login_wrong_password(self, svc, mock_repo):
        pw_hash = _hash_password("correct")
        mock_repo.get_by_email.return_value = AsyncMock(
            id=uuid.uuid4(), password_hash=pw_hash, is_active=True
        )
        with pytest.raises(AuthenticationError):
            await svc.login("user@test.com", "wrong")

    async def test_login_nonexistent_email(self, svc, mock_repo):
        mock_repo.get_by_email.return_value = None
        with pytest.raises(AuthenticationError):
            await svc.login("nobody@test.com", "password")

    async def test_login_disabled_account(self, svc, mock_repo):
        mock_repo.get_by_email.return_value = AsyncMock(
            id=uuid.uuid4(), password_hash=_hash_password("pw"), is_active=False
        )
        with pytest.raises(AuthenticationError):
            await svc.login("disabled@test.com", "pw")
