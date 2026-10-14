import pytest
from unittest.mock import AsyncMock, MagicMock
from app.security import check_admin_auth, hash_api_key, mask_api_key
import main


def test_mask_and_hash_api_key():
    # Gemini key masking
    gemini_key = "AIzaSyABCDEF1234567890abcdef9876543210"
    masked = mask_api_key(gemini_key)
    assert masked.startswith("AIzaSy...")
    assert masked.endswith("3210")
    assert gemini_key not in masked  # Raw full key must never be visible

    # Anthropic key masking
    ant_key = "sk-ant-api03-0123456789abcdef0123456789"
    masked_ant = mask_api_key(ant_key)
    assert masked_ant.startswith("sk-ant...")
    assert masked_ant.endswith("6789")

    # Short / None / Bearer stripped
    assert mask_api_key(None) == "not-configured"
    assert mask_api_key("") == "not-configured"
    assert mask_api_key("bearer AIzaSyABCDEF1234567890abcdef9876543210").startswith("AIzaSy...")

    # Deterministic hash
    h1 = hash_api_key("my-secret-key-1")
    h2 = hash_api_key("my-secret-key-1")
    h3 = hash_api_key("my-secret-key-2")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 16


@pytest.mark.asyncio
async def test_admin_auth_checks(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "super-secret-admin-pass")

    # Reject unauthorized
    resp = await async_client.get("/admin/connected-users")
    assert resp.status_code == 401
    assert "admin privileges required" in resp.json()["error"]

    resp = await async_client.get("/admin/verify")
    assert resp.status_code == 401

    # Accept with X-Admin-Token
    headers = {"X-Admin-Token": "super-secret-admin-pass"}
    resp = await async_client.get("/admin/verify", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert resp.json()["role"] == "admin"

    # Accept with query param ?admin_token=...
    resp = await async_client.get("/admin/verify?admin_token=super-secret-admin-pass")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_connected_users_mocked(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "admin-key")

    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "key_hash": "hash123",
            "session_id": "alex",
            "project": "ecommerce",
            "key_masked": "AIzaSy...7890",
            "provider": "gemini",
            "models_used": ["gemini-3.1-flash-lite-preview"],
            "first_seen": None,
            "last_seen": None,
            "total_calls": 14,
            "total_input_tokens": 1200,
            "total_output_tokens": 400
        }
    ])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    headers = {"X-Admin-Token": "admin-key"}
    resp = await async_client.get("/admin/connected-users", headers=headers)
    assert resp.status_code == 200
    users = resp.json()["users"]
    assert len(users) == 1
    assert users[0]["session_id"] == "alex"
    assert users[0]["key_masked"] == "AIzaSy...7890"
    assert users[0]["provider"] == "gemini"


@pytest.mark.asyncio
async def test_user_profile_endpoint(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetchrow = AsyncMock(return_value={
        "session_id": "sarah",
        "project": "finance-agent",
        "key_masked": "sk-ant...9999",
        "provider": "anthropic",
        "models_used": ["claude-3-5-sonnet"],
        "first_seen": None,
        "last_seen": None,
        "total_calls": 5,
    })
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    resp = await async_client.get("/user/profile?user=sarah")
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert profile["session_id"] == "sarah"
    assert profile["key_masked"] == "sk-ant...9999"
    assert profile["provider"] == "anthropic"


@pytest.mark.asyncio
async def test_stats_user_isolation(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "admin-key")

    # Regular user requesting without admin token must be rejected if no session_id is given
    resp = await async_client.get("/stats")
    assert resp.status_code == 401
    assert "admin privileges or developer session_id required" in resp.json()["error"]

    # When regular user passes their session_id, they get their own metrics
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "model": "gemini-3.1-flash-lite-preview",
            "calls": 2,
            "avg_latency_ms": 300,
            "input_tokens": 100,
            "output_tokens": 20,
            "passes": 2,
            "fails": 0
        }
    ])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire
    monkeypatch.setattr(main, "pool", mock_pool)

    resp = await async_client.get("/stats?session_id=developer-bob")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["model"] == "gemini-3.1-flash-lite-preview"
