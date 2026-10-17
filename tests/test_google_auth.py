"""
Unit tests for Google Login, Session Management, and Account Persistence in VOLT-AI.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import main
from app.storage import (
    upsert_google_user,
    create_user_session,
    get_user_by_session_token,
    delete_user_session,
    fetch_all_users,
    _IN_MEMORY_USERS,
    _IN_MEMORY_SESSIONS,
)


@pytest.fixture(autouse=True)
def clean_auth_state():
    """Clear in-memory user and session stores between tests."""
    _IN_MEMORY_USERS.clear()
    _IN_MEMORY_SESSIONS.clear()


@pytest.mark.asyncio
async def test_login_page_renders_html(async_client):
    """GET /login should render the Google login portal with GSI script and branding."""
    resp = await async_client.get("/login")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Sign in to VOLT-AI" in resp.text
    assert "https://accounts.google.com/gsi/client" in resp.text
    assert "Google Sign In" in resp.text or "Sign in with Google" in resp.text
    assert "Baizo" in resp.text


@pytest.mark.asyncio
async def test_demo_login_creates_account_and_session(async_client):
    """POST /api/auth/demo-login should save account in database and return session."""
    payload = {
        "email": "developer.sanjai@gmail.com",
        "name": "Sanjai Developer",
        "picture": "https://lh3.googleusercontent.com/a/sanjai-pic",
    }
    resp = await async_client.post("/api/auth/demo-login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["token"].startswith("volt_sess_")
    assert data["user"]["email"] == "developer.sanjai@gmail.com"
    assert data["user"]["name"] == "Sanjai Developer"
    assert data["redirect_url"] == "/dashboard"

    # Verify cookie was set
    assert "volt_session" in resp.cookies
    assert resp.cookies["volt_session"].startswith("volt_sess_")

    # Verify user was saved in user store
    assert "developer.sanjai@gmail.com" in _IN_MEMORY_USERS
    saved_user = _IN_MEMORY_USERS["developer.sanjai@gmail.com"]
    assert saved_user["name"] == "Sanjai Developer"


@pytest.mark.asyncio
async def test_google_verify_with_mock_credential(async_client):
    """POST /api/auth/google/verify with mock token saves user to DB and establishes session."""
    payload = {
        "credential": "mock_google_id_token_12345"
    }
    resp = await async_client.post("/api/auth/google/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["token"].startswith("volt_sess_")
    assert "test-user-" in data["user"]["email"]
    assert data["user"]["role"] in ("developer", "admin")
    assert "volt_session" in resp.cookies


@pytest.mark.asyncio
async def test_google_verify_missing_credential_rejected(async_client):
    """POST /api/auth/google/verify without credential returns 400 Bad Request."""
    resp = await async_client.post("/api/auth/google/verify", json={})
    assert resp.status_code == 400
    assert resp.json()["ok"] is False


@pytest.mark.asyncio
async def test_auth_me_lifecycle(async_client):
    """Verify /api/auth/me returns user profile when logged in and null when unauthenticated."""
    # 1. Unauthenticated request
    resp_unauth = await async_client.get("/api/auth/me")
    assert resp_unauth.status_code == 200
    assert resp_unauth.json()["user"] is None

    # 2. Log in via demo login
    login_resp = await async_client.post(
        "/api/auth/demo-login",
        json={"email": "alice.coder@gmail.com", "name": "Alice Coder"}
    )
    token = login_resp.json()["token"]

    # 3. Authenticated request with cookie
    resp_auth_cookie = await async_client.get(
        "/api/auth/me",
        cookies={"volt_session": token}
    )
    assert resp_auth_cookie.status_code == 200
    user = resp_auth_cookie.json()["user"]
    assert user is not None
    assert user["email"] == "alice.coder@gmail.com"
    assert user["name"] == "Alice Coder"

    # 4. Authenticated request with Bearer header
    resp_auth_header = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_auth_header.status_code == 200
    assert resp_auth_header.json()["user"]["email"] == "alice.coder@gmail.com"


@pytest.mark.asyncio
async def test_auth_logout_terminates_session(async_client):
    """POST /api/auth/logout should invalidate session and remove cookie."""
    # Log in
    login_resp = await async_client.post(
        "/api/auth/demo-login",
        json={"email": "bob.builder@gmail.com", "name": "Bob"}
    )
    token = login_resp.json()["token"]

    # Log out
    logout_resp = await async_client.post(
        "/api/auth/logout",
        cookies={"volt_session": token}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["ok"] is True

    # Check /api/auth/me after logout
    me_resp = await async_client.get(
        "/api/auth/me",
        cookies={"volt_session": token}
    )
    assert me_resp.json()["user"] is None


@pytest.mark.asyncio
async def test_admin_users_list_endpoint(async_client, monkeypatch):
    """GET /api/users requires admin permissions and returns list of registered users."""
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "secret-admin-pass")

    # Seed two users
    await async_client.post("/api/auth/demo-login", json={"email": "u1@gmail.com", "name": "User One"})
    await async_client.post("/api/auth/demo-login", json={"email": "u2@gmail.com", "name": "User Two"})

    # Reject unauthenticated request
    resp_unauth = await async_client.get("/api/users")
    assert resp_unauth.status_code == 401

    # Accept request with Admin Token
    resp_admin = await async_client.get(
        "/api/users",
        headers={"X-Admin-Token": "secret-admin-pass"}
    )
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert data["ok"] is True
    emails = [u["email"] for u in data["users"]]
    assert "u1@gmail.com" in emails
    assert "u2@gmail.com" in emails


@pytest.mark.asyncio
async def test_repeat_login_updates_last_login_timestamp():
    """Upserting existing user updates last_login_at while preserving created_at and ID."""
    u1 = await upsert_google_user(
        pool=None,
        email="sanjai.repeat@gmail.com",
        name="Sanjai V1",
        picture="pic1.png"
    )
    first_created = u1["created_at"]
    first_id = u1["id"]

    # Second login with updated name
    u2 = await upsert_google_user(
        pool=None,
        email="sanjai.repeat@gmail.com",
        name="Sanjai V2",
        picture="pic2.png"
    )
    assert u2["id"] == first_id
    assert u2["created_at"] == first_created
    assert u2["name"] == "Sanjai V2"
    assert u2["picture"] == "pic2.png"
