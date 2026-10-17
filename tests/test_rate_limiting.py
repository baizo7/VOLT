"""
Unit tests for burst rate limiting and CORS middleware.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
import main


@pytest.mark.asyncio
async def test_cors_headers_present():
    """Verify that CORS middleware exposes all VOLT headers and allows origins."""
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.options(
            "/v1/chat/completions",
            headers={
                "Origin": "https://dashboard.volt-ai.dev",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            }
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") in ("*", "https://dashboard.volt-ai.dev")
        assert "POST" in resp.headers.get("access-control-allow-methods", "")


@pytest.mark.asyncio
async def test_burst_rate_limiting_exceeded(monkeypatch):
    """Verify that unauthenticated requests exceeding burst limit return 429."""
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.setenv("VOLT_RATE_LIMIT", "1")
    monkeypatch.setenv("VOLT_BURST_RATE_LIMIT", "3/minute")
    main.limiter.reset()

    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 5}
    }
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(main, "client", mock_client)

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "model": "VOLT-AI",
            "messages": [{"role": "user", "content": "hi"}],
        }

        # First 3 requests succeed
        for _ in range(3):
            r = await client.post(
                "/v1/chat/completions",
                json=payload,
                headers={"x-forwarded-for": "203.0.113.195"}
            )
            assert r.status_code == 200

        # 4th request exceeds burst limit and receives 429
        r4 = await client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"x-forwarded-for": "203.0.113.195"}
        )
        assert r4.status_code == 429
        data = r4.json()
        assert "error" in data
        assert data["error"]["type"] == "rate_limit_exceeded"
        assert r4.headers.get("retry-after") == "60"
        assert r4.headers.get("x-volt-rate-limit") == "exceeded"


@pytest.mark.asyncio
async def test_byok_keys_bypass_community_rate_limit(monkeypatch):
    """Verify that developers providing their own API key (BYOK) receive higher quota."""
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.setenv("VOLT_RATE_LIMIT", "1")
    monkeypatch.setenv("VOLT_BURST_RATE_LIMIT", "2/minute")
    main.limiter.reset()

    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 5}
    }
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(main, "client", mock_client)

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "model": "VOLT-AI",
            "messages": [{"role": "user", "content": "hi"}],
        }

        # 4 requests with BYOK provider key all succeed beyond the 2/minute community limit
        for _ in range(4):
            r = await client.post(
                "/v1/chat/completions",
                json=payload,
                headers={
                    "Authorization": "Bearer sk-or-v1-byok-developer-key-unlimited",
                    "x-forwarded-for": "203.0.113.196"
                }
            )
            assert r.status_code == 200
