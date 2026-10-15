"""SEC-01 / SEC-02: inactive users can neither log in nor use previously issued tokens."""

from app.core.security import create_access_token
from app.db.models.user import UserRole


def token_for(user):
    return create_access_token(user_id=str(user.id), role=user.role.value)


def auth(user):
    return {"Authorization": f"Bearer {token_for(user)}"}


# --- SEC-01: login ---------------------------------------------------------


def test_active_user_can_login(client, password, make_user):
    make_user("active@example.com")

    r = client.post("/api/v1/auth/login", json={"email": "active@example.com", "password": password})

    assert r.status_code == 200
    assert r.json()["access_token"]


def test_inactive_user_cannot_login(client, password, make_user):
    make_user("inactive@example.com", is_active=False)

    r = client.post("/api/v1/auth/login", json={"email": "inactive@example.com", "password": password})

    assert r.status_code == 401
    assert "access_token" not in r.json()


def test_inactive_login_error_matches_wrong_password(client, password, make_user):
    make_user("inactive@example.com", is_active=False)
    make_user("active@example.com")

    inactive = client.post("/api/v1/auth/login", json={"email": "inactive@example.com", "password": password})
    wrong_pw = client.post("/api/v1/auth/login", json={"email": "active@example.com", "password": "wrong-password"})

    assert inactive.status_code == wrong_pw.status_code == 401
    assert inactive.json() == wrong_pw.json() == {"detail": "Invalid email or password"}


def test_inactive_user_with_wrong_password_gets_generic_error(client, make_user):
    make_user("inactive@example.com", is_active=False)

    r = client.post("/api/v1/auth/login", json={"email": "inactive@example.com", "password": "wrong-password"})

    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid email or password"}


# --- SEC-02: protected endpoints with an already-issued token --------------


def test_active_user_can_access_me(client, make_user):
    user = make_user("active@example.com")

    r = client.get("/api/v1/auth/me", headers=auth(user))

    assert r.status_code == 200
    assert r.json()["email"] == "active@example.com"


def test_inactive_user_token_rejected_on_me(client, make_user):
    user = make_user("inactive@example.com", is_active=False)

    r = client.get("/api/v1/auth/me", headers=auth(user))

    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid or expired token"}


def test_token_rejected_after_user_deactivated(client, make_user):
    user = make_user("active@example.com")
    headers = auth(user)
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

    user.is_active = False

    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid or expired token"}


def test_active_admin_can_access_dashboard(client, make_user):
    admin = make_user("admin@example.com", role=UserRole.ADMIN)

    r = client.get("/api/v1/admin/dashboard", headers=auth(admin))

    assert r.status_code == 200


def test_inactive_admin_rejected_on_role_protected_route(client, make_user):
    admin = make_user("admin@example.com", role=UserRole.ADMIN, is_active=False)

    r = client.get("/api/v1/admin/dashboard", headers=auth(admin))

    # 401 (not 403): the account itself is rejected before any role check.
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid or expired token"}


def test_inactive_and_deleted_users_get_identical_response(client, make_user, users):
    inactive = make_user("inactive@example.com", is_active=False)
    deleted = make_user("deleted@example.com")
    deleted_headers = auth(deleted)
    del users[deleted.id]

    a = client.get("/api/v1/auth/me", headers=auth(inactive))
    b = client.get("/api/v1/auth/me", headers=deleted_headers)

    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_inactive_user_rejection_sends_bearer_challenge(client, make_user):
    user = make_user("inactive@example.com", is_active=False)

    r = client.get("/api/v1/auth/me", headers=auth(user))

    assert r.status_code == 401
    assert r.headers["WWW-Authenticate"] == "Bearer"


# --- /users (ADMIN, MANAGER) -----------------------------------------------


def test_active_manager_can_list_users(client, make_user):
    manager = make_user("manager@example.com", role=UserRole.MANAGER)
    make_user("someone@example.com")

    r = client.get("/api/v1/users", headers=auth(manager))

    assert r.status_code == 200
    assert {u["email"] for u in r.json()} == {"manager@example.com", "someone@example.com"}


def test_inactive_manager_cannot_list_users(client, make_user):
    manager = make_user("manager@example.com", role=UserRole.MANAGER, is_active=False)

    r = client.get("/api/v1/users", headers=auth(manager))

    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid or expired token"}
    assert r.headers["WWW-Authenticate"] == "Bearer"


# --- Unchanged active-user behavior ----------------------------------------


def test_active_user_role_is_forbidden_from_users_list(client, make_user):
    user = make_user("user@example.com")

    r = client.get("/api/v1/users", headers=auth(user))

    assert r.status_code == 403
    assert r.json() == {"detail": "Insufficient permissions"}


def test_active_manager_is_forbidden_from_admin_dashboard(client, make_user):
    manager = make_user("manager@example.com", role=UserRole.MANAGER)

    r = client.get("/api/v1/admin/dashboard", headers=auth(manager))

    assert r.status_code == 403


def test_missing_token_still_returns_not_authenticated(client):
    r = client.get("/api/v1/auth/me")

    assert r.status_code == 401
    assert r.json() == {"detail": "Not authenticated"}
    assert r.headers["WWW-Authenticate"] == "Bearer"


def test_unknown_email_login_unchanged(client, users):
    r = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever-pass"})

    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid email or password"}
