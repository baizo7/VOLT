import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
import main
from app.router import (
    calculate_pass_rate,
    select_optimal_model,
    resolve_dynamic_route,
    RouterDecision,
    DEFAULT_FALLBACK_MODEL,
)


def test_calculate_pass_rate():
    assert calculate_pass_rate(0, 0) == 0.0
    # 9 passes, 1 fail -> (9+1)/(10+2) = 10/12 = 0.8333
    assert calculate_pass_rate(9, 1) == 0.8333
    # 0 passes, 1 fail -> 1/3 = 0.3333
    assert calculate_pass_rate(0, 1) == 0.3333


def test_select_optimal_model_empty_stats():
    decision = select_optimal_model([])
    assert decision.is_fallback is True
    assert decision.selected_model == DEFAULT_FALLBACK_MODEL


def test_select_optimal_model_best_pass_rate():
    stats = [
        {"model": "model-a", "passes": 1, "fails": 5, "calls": 6, "avg_latency_ms": 300},
        {"model": "model-b", "passes": 9, "fails": 1, "calls": 10, "avg_latency_ms": 1200},
        {"model": "model-c", "passes": 5, "fails": 5, "calls": 10, "avg_latency_ms": 500},
    ]
    decision = select_optimal_model(stats, strategy="best_pass_rate")
    assert decision.selected_model == "model-b"
    assert decision.is_fallback is False
    assert decision.metrics["passes"] == 9


def test_select_optimal_model_lowest_latency():
    stats = [
        {"model": "model-a", "passes": 1, "fails": 5, "calls": 6, "avg_latency_ms": 250},
        {"model": "model-b", "passes": 9, "fails": 1, "calls": 10, "avg_latency_ms": 1200},
        {"model": "model-c", "passes": 5, "fails": 5, "calls": 10, "avg_latency_ms": 500},
    ]
    decision = select_optimal_model(stats, strategy="lowest_latency")
    assert decision.selected_model == "model-a"
    assert decision.metrics["avg_latency_ms"] == 250


def test_select_optimal_model_max_latency_constraint():
    stats = [
        {"model": "model-slow-best", "passes": 20, "fails": 0, "calls": 20, "avg_latency_ms": 3000},
        {"model": "model-fast-ok", "passes": 8, "fails": 2, "calls": 10, "avg_latency_ms": 600},
    ]
    # Restrict to max 1000ms latency
    decision = select_optimal_model(stats, strategy="best_pass_rate", max_latency_ms=1000)
    assert decision.selected_model == "model-fast-ok"


def test_select_optimal_model_candidate_filter():
    stats = [
        {"model": "model-x", "passes": 10, "fails": 0, "calls": 10, "avg_latency_ms": 500},
        {"model": "model-y", "passes": 5, "fails": 1, "calls": 6, "avg_latency_ms": 600},
    ]
    decision = select_optimal_model(stats, candidate_models=["model-y"])
    assert decision.selected_model == "model-y"


@pytest.mark.asyncio
async def test_resolve_dynamic_route_direct():
    decision = await resolve_dynamic_route(None, "gpt-4", {})
    assert decision.strategy == "direct"
    assert decision.selected_model == "gpt-4"
    assert decision.is_fallback is False


@pytest.mark.asyncio
async def test_resolve_dynamic_route_auto_pool_none():
    decision = await resolve_dynamic_route(None, "auto", {})
    assert decision.is_fallback is True
    assert decision.selected_model == DEFAULT_FALLBACK_MODEL


@pytest.mark.asyncio
async def test_proxy_dynamic_model_routing_auto(async_client, monkeypatch):
    captured_request = {}

    def mock_handler(request: httpx.Request):
        captured_request["body"] = request.read().decode("utf-8")
        return httpx.Response(200, json={"choices": [{"message": {"content": "routed output"}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    # Mock DB pool with stats returning deepseek as top model
    mock_stats = [
        {"model": "claude", "passes": 2, "fails": 8, "calls": 10, "avg_latency_ms": 1200},
        {"model": "deepseek", "passes": 9, "fails": 1, "calls": 10, "avg_latency_ms": 400},
    ]

    mock_pool = MagicMock()
    monkeypatch.setattr(main, "pool", mock_pool)

    async def mock_fetch_stats(p):
        return mock_stats

    monkeypatch.setattr("app.storage.fetch_stats", mock_fetch_stats)

    payload = {
        "model": "auto",
        "messages": [{"role": "user", "content": "solve this task"}]
    }

    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    assert resp.headers.get("x-observer-routed-model") == "deepseek"
    assert resp.headers.get("x-observer-route-strategy") == "best_pass_rate"

    # Upstream request body model should have been mutated to deepseek
    import json
    sent_body = json.loads(captured_request["body"])
    assert sent_body["model"] == "deepseek"


@pytest.mark.asyncio
async def test_router_recommendations_endpoint(async_client, monkeypatch):
    mock_stats = [
        {"model": "fast-model", "passes": 5, "fails": 5, "calls": 10, "avg_latency_ms": 150},
        {"model": "accurate-model", "passes": 10, "fails": 0, "calls": 10, "avg_latency_ms": 800},
    ]

    mock_pool = MagicMock()
    monkeypatch.setattr(main, "pool", mock_pool)

    async def mock_fetch_stats(p):
        return mock_stats

    monkeypatch.setattr("app.storage.fetch_stats", mock_fetch_stats)

    resp = await async_client.get("/router/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    recs = data["recommendations"]
    assert recs["best_pass_rate"]["model"] == "accurate-model"
    assert recs["lowest_latency"]["model"] == "fast-model"
