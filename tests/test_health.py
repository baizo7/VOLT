import pytest
from unittest.mock import AsyncMock, MagicMock
import main


@pytest.mark.asyncio
async def test_health_503_when_pool_is_none(async_client, monkeypatch):
    monkeypatch.setattr(main, "pool", None)
    resp = await async_client.get("/health")
    assert resp.status_code == 503
    data = resp.json()
    assert data["ok"] is False
    assert data["status"] == "unready"


@pytest.mark.asyncio
async def test_health_503_when_db_ping_fails(async_client, monkeypatch):
    mock_pool = MagicMock()
    # Mock acquire context manager to raise an error
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.side_effect = RuntimeError("Connection refused")
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)
    resp = await async_client.get("/health")
    assert resp.status_code == 503
    data = resp.json()
    assert data["ok"] is False
    assert data["status"] == "unready"


@pytest.mark.asyncio
async def test_health_200_when_db_ping_succeeds(async_client, monkeypatch):
    mock_conn = MagicMock()
    mock_conn.fetchval = AsyncMock(return_value=1)

    mock_pool = MagicMock()
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["status"] == "ready"
