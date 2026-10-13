import pytest
from main import resolve_route, DEFAULT_BASE


def test_routing_prefix_match():
    r1 = resolve_route("claude-3-5-sonnet-20241022", "anthropic")
    assert r1["base_url"] == "https://api.anthropic.com"

    r2 = resolve_route("deepseek-chat", "openai")
    assert r2["base_url"] == "https://api.deepseek.com/v1"
    assert r2["api_key_env"] == "DEEPSEEK_API_KEY"


def test_routing_slash_prefix():
    r = resolve_route("nvidia/llama-3.1-nemotron-70b-instruct", "openai")
    assert r["base_url"] == "https://openrouter.ai/api/v1"
    assert r["api_key_env"] == "OPENROUTER_API_KEY"


def test_routing_wildcard_fallback():
    r = resolve_route("meta-llama/llama-3-8b", "openai")
    assert r["base_url"] == "https://openrouter.ai/api/v1"
    assert r["api_key_env"] == "OPENROUTER_API_KEY"


def test_routing_no_wildcard_default():
    import main
    saved = main.routes
    try:
        main.routes = {"gpt-4": {"base_url": "https://api.openai.com/v1", "api_key_env": "OPENAI_KEY"}}
        r_openai = resolve_route("unknown-model", "openai")
        assert r_openai["base_url"] == DEFAULT_BASE["openai"]

        r_anthropic = resolve_route("unknown-model", "anthropic")
        assert r_anthropic["base_url"] == DEFAULT_BASE["anthropic"]
    finally:
        main.routes = saved
