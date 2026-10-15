"""Test that SEC-01/02 integration preserves refresh-token functionality."""

import pytest
from app.core.security import decode_access_token


def test_active_user_login_issues_access_and_refresh_tokens(client, password, make_user, refresh_tokens):
    user = make_user("refresh_active@example.com")

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh_active@example.com", "password": password},
    )

    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Token payload matches active user
    payload = decode_access_token(data["access_token"])
    assert payload["sub"] == str(user.id)
    assert payload["role"] == user.role.value

    # Refresh token was persisted to repository store
    assert len(refresh_tokens) == 1
    stored_token = next(iter(refresh_tokens.values()))
    assert stored_token.user_id == user.id


def test_inactive_user_login_does_not_issue_or_persist_refresh_token(client, password, make_user, refresh_tokens):
    make_user("refresh_inactive@example.com", is_active=False)

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh_inactive@example.com", "password": password},
    )

    assert r.status_code == 401
    assert "refresh_token" not in r.json()
    assert "access_token" not in r.json()
    assert len(refresh_tokens) == 0
