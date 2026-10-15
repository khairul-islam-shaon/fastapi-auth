import os
from unittest.mock import AsyncMock

# Settings are read at import time; set them before importing the app.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-long-enough-for-hs256")

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.main import app
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


PASSWORD = "correct-password"
# Argon2 is deliberately slow; hash once per test session.
PASSWORD_HASH = hash_password(PASSWORD)


@pytest.fixture
def users(monkeypatch):
    """In-memory user store backing UserRepository lookups; no database needed."""
    store: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id):
        return store.get(user_id)

    async def get_by_email(self, email):
        return next((u for u in store.values() if u.email == email), None)

    async def list_users(self):
        return list(store.values())

    monkeypatch.setattr(UserRepository, "get_by_id", get_by_id)
    monkeypatch.setattr(UserRepository, "get_by_email", get_by_email)
    monkeypatch.setattr(UserRepository, "list_users", list_users)
    return store


@pytest.fixture(autouse=True)
def refresh_tokens(monkeypatch):
    """In-memory refresh token store backing RefreshTokenRepository lookups; no database needed."""
    store: dict[str, RefreshToken] = {}

    async def create(self, user_id, token_hash, expires_at):
        refresh_token = RefreshToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        store[token_hash] = refresh_token
        return refresh_token

    async def get_by_hash(self, token_hash):
        return store.get(token_hash)

    async def revoke(self, refresh_token, revoked_at):
        refresh_token.revoked_at = revoked_at
        return refresh_token

    monkeypatch.setattr(RefreshTokenRepository, "create", create)
    monkeypatch.setattr(RefreshTokenRepository, "get_by_hash", get_by_hash)
    monkeypatch.setattr(RefreshTokenRepository, "revoke", revoke)
    return store


@pytest.fixture
def password():
    return PASSWORD


@pytest.fixture
def make_user(users):
    def _make(email, role=UserRole.USER, is_active=True):
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=PASSWORD_HASH,
            full_name=None,
            role=role,
            is_active=is_active,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        users[user.id] = user
        return user

    return _make


@pytest.fixture
def client():
    async def no_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = no_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
