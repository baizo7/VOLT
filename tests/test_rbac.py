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
    main.ADMIN_FAILED_ATTEMPTS.clear()

    # Reject unauthorized / missing token
    resp = await async_client.get("/admin/connected-users")
    assert resp.status_code == 401
    assert "admin privileges required" in resp.json()["error"]

    resp = await async_client.get("/admin/verify")
    assert resp.status_code == 401

    # Reject wrong key
    resp_wrong = await async_client.get("/admin/verify", headers={"X-Admin-Token": "wrong-password"})
    assert resp_wrong.status_code == 401

    # Accept with X-Admin-Token
    headers = {"X-Admin-Token": "super-secret-admin-pass"}
    resp = await async_client.get("/admin/verify", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert resp.json()["role"] == "admin"

    # Accept with query param ?admin_token=...
    resp = await async_client.get("/admin/verify?admin_token=super-secret-admin-pass")
    assert resp.status_code == 200

    # Accept with POST JSON body
    resp_post = await async_client.post("/admin/verify", json={"admin_key": "super-secret-admin-pass"})
    assert resp_post.status_code == 200
    assert resp_post.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_admin_auth_unset_key_strictly_denies(async_client, monkeypatch):
    monkeypatch.delenv("OBSERVER_ADMIN_KEY", raising=False)
    monkeypatch.delenv("OBSERVER_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("OBSERVER_AUTH_TOKEN", raising=False)
    main.ADMIN_FAILED_ATTEMPTS.clear()

    # Even if someone sends a token or query, unset admin key strictly denies access
    resp = await async_client.get("/admin/verify?admin_token=anything")
    assert resp.status_code == 401
    assert "invalid admin key" in resp.json()["error"]


@pytest.mark.asyncio
async def test_admin_verify_brute_force_lockout(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "super-secret-admin-pass")
    main.ADMIN_FAILED_ATTEMPTS.clear()

    # Send 5 incorrect attempts
    for i in range(5):
        resp = await async_client.post("/admin/verify", json={"admin_key": f"bad-attempt-{i}"})
        assert resp.status_code == 401

    # 6th attempt should be locked out with 429 Too Many Requests
    resp_locked = await async_client.post("/admin/verify", json={"admin_key": "super-secret-admin-pass"})
    assert resp_locked.status_code == 429
    assert "Too many failed admin login attempts" in resp_locked.json()["error"]
    assert "Retry-After" in resp_locked.headers



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


@pytest.mark.asyncio
async def test_task_trace_rbac_isolation(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "admin-key")

    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetchrow = AsyncMock(return_value={
        "task_id": "task_secret",
        "project": "security-audit",
        "task_type": "coding",
        "title": "Fix vuln",
        "created_at": None,
    })
    def make_mock_fetch():
        return AsyncMock(side_effect=[
            [{
                "id": "c1",
                "ts": None,
                "session_id": "alice",
                "model": "qwen2.5-coder-7b",
                "upstream": "https://api.openai.com",
                "api_style": "openai",
                "streamed": False,
                "status_code": 200,
                "latency_ms": 120,
                "input_tokens": 50,
                "output_tokens": 100,
                "error": None,
            }],
            [{
                "id": 1,
                "kind": "test",
                "status": "pass",
                "details": "{}",
                "created_at": None,
            }],
        ])

    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire
    monkeypatch.setattr(main, "pool", mock_pool)

    # 1. Bob attempts to view Alice's task trace -> 403 Forbidden
    mock_conn.fetch = make_mock_fetch()
    resp_bob = await async_client.get("/tasks/task_secret", headers={"X-Session-Id": "bob"})
    assert resp_bob.status_code == 403
    assert "cannot access other developers' task traces" in resp_bob.json()["error"]

    # 2. Anonymous/no-session request without admin key -> 401 Unauthorized
    mock_conn.fetch = make_mock_fetch()
    resp_anon = await async_client.get("/tasks/task_secret")
    assert resp_anon.status_code == 401

    # 3. Alice views her own task trace -> 200 OK
    mock_conn.fetch = make_mock_fetch()
    resp_alice = await async_client.get("/tasks/task_secret", headers={"X-Session-Id": "alice"})
    assert resp_alice.status_code == 200
    assert resp_alice.json()["task"]["task_id"] == "task_secret"

    # 4. Admin views the task trace -> 200 OK
    mock_conn.fetch = make_mock_fetch()
    resp_admin = await async_client.get("/tasks/task_secret", headers={"X-Admin-Token": "admin-key"})
    assert resp_admin.status_code == 200
    assert resp_admin.json()["task"]["task_id"] == "task_secret"


@pytest.mark.asyncio
async def test_session_spoofing_prevention(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "admin-key")

    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire
    monkeypatch.setattr(main, "pool", mock_pool)

    alice_headers = {"X-Session-Id": "alice"}

    # /stats: Alice cannot snoop on Bob's statistics
    resp = await async_client.get("/stats?session_id=bob", headers=alice_headers)
    assert resp.status_code == 403
    assert "cannot access other developers' statistics" in resp.json()["error"]

    # /tasks: Alice cannot snoop on Bob's tasks
    resp = await async_client.get("/tasks?session_id=bob", headers=alice_headers)
    assert resp.status_code == 403
    assert "cannot access other developers' tasks" in resp.json()["error"]

    # /stats/timeseries: Alice cannot snoop on Bob's timeseries
    resp = await async_client.get("/stats/timeseries?session_id=bob", headers=alice_headers)
    assert resp.status_code == 403
    assert "cannot access other developers' timeseries" in resp.json()["error"]

    # /user/profile: Alice cannot view Bob's profile
    resp = await async_client.get("/user/profile?user=bob", headers=alice_headers)
    assert resp.status_code == 403
    assert "cannot access other developers' profiles" in resp.json()["error"]


@pytest.mark.asyncio
async def test_admin_global_access_and_dataset_stats(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "admin-key")

    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire
    monkeypatch.setattr(main, "pool", mock_pool)

    # 1. Non-admin attempting to access /admin/dataset/stats is rejected
    resp = await async_client.get("/admin/dataset/stats")
    assert resp.status_code == 401

    # 2. Admin can access /admin/dataset/stats
    monkeypatch.setattr("main.export_sft_dataset", AsyncMock(return_value=[]))
    monkeypatch.setattr("main.export_dpo_dataset", AsyncMock(return_value=[]))
    resp = await async_client.get("/admin/dataset/stats", headers={"X-Admin-Token": "admin-key"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # 3. Admin can view any user profile
    mock_conn.fetchrow = AsyncMock(return_value={
        "session_id": "bob",
        "project": "proj-b",
        "key_masked": "sk-ant...1234",
        "provider": "anthropic",
        "models_used": ["claude-3-5-sonnet"],
        "first_seen": None,
        "last_seen": None,
        "total_calls": 10,
    })
    resp = await async_client.get("/user/profile?user=bob", headers={"X-Admin-Token": "admin-key"})
    assert resp.status_code == 200
    assert resp.json()["profile"]["session_id"] == "bob"

