import pytest
from unittest.mock import AsyncMock, MagicMock
import main


@pytest.mark.asyncio
async def test_stats_endpoint_mocked(async_client, monkeypatch):
    mock_conn = MagicMock()
    mock_rows = [
        {
            "model": "deepseek-chat",
            "calls": 10,
            "avg_latency_ms": 450,
            "input_tokens": 12000,
            "output_tokens": 3000,
            "passes": 8,
            "fails": 2
        },
        {
            "model": "claude-3-5-sonnet",
            "calls": 5,
            "avg_latency_ms": 780,
            "input_tokens": 8000,
            "output_tokens": 2000,
            "passes": 5,
            "fails": 0
        }
    ]
    mock_conn.fetch = AsyncMock(return_value=mock_rows)

    mock_pool = MagicMock()
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    resp = await async_client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["model"] == "deepseek-chat"
    assert data[0]["passes"] == 8
    assert data[0]["fails"] == 2
    assert data[1]["model"] == "claude-3-5-sonnet"
    assert data[1]["passes"] == 5


def test_stats_query_contains_distinct_attribution():
    # Verify that the query in main.py uses DISTINCT ON (task_id) for single attribution
    import inspect
    source = inspect.getsource(main.stats)
    assert "DISTINCT ON (task_id)" in source
    assert "task_primary_model" in source


@pytest.mark.asyncio
async def test_stats_timeseries_endpoint(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "day": "2026-10-14",
            "model": "gpt-4o",
            "calls": 25,
            "avg_latency_ms": 320,
            "input_tokens": 5000,
            "output_tokens": 1500,
        }
    ])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    # Valid request
    resp = await async_client.get("/stats/timeseries?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["days"] == 7
    assert len(data["series"]) == 1
    assert data["series"][0]["model"] == "gpt-4o"

    # Invalid days (< 1 or > 365)
    resp_low = await async_client.get("/stats/timeseries?days=0")
    assert resp_low.status_code == 400
    resp_high = await async_client.get("/stats/timeseries?days=400")
    assert resp_high.status_code == 400

