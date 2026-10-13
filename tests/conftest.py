import os
import json
import pytest
from httpx import AsyncClient, ASGITransport
import main


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure tests run with a clean auth state unless explicitly set."""
    monkeypatch.delenv("OBSERVER_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("OBSERVER_TOKEN", raising=False)
    # Ensure default test routes
    main.routes = {
        "local/": {"base_url": "http://127.0.0.1:8080/v1", "api_key_env": None},
        "claude": {"base_url": "https://api.anthropic.com", "api_key_env": None},
        "deepseek": {"base_url": "https://api.deepseek.com/v1", "api_key_env": "DEEPSEEK_API_KEY"},
        "nvidia/": {"base_url": "https://openrouter.ai/api/v1", "api_key_env": "OPENROUTER_API_KEY"},
        "*": {"base_url": "https://openrouter.ai/api/v1", "api_key_env": "OPENROUTER_API_KEY"}
    }


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
