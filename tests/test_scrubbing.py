import pytest
from main import scrub_text, scrub_json, scrub_record, log_call, SECRET_PATTERNS


def test_scrub_existing_patterns():
    # OpenAI sk-
    assert scrub_text("key: sk-1234567890abcdef123456") == "key: [REDACTED]"
    # AWS AKIA
    assert scrub_text("access AKIAIOSFODNN7EXAMPLE") == "access [REDACTED]"
    # GitHub ghp_
    assert scrub_text("token: ghp_12345678901234567890123456789012") == "token: [REDACTED]"
    # Bearer token
    assert scrub_text("Authorization: Bearer mysecrettoken12345678") == "Authorization: [REDACTED]"
    # Private key
    pk = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----"
    assert scrub_text(pk) == "[REDACTED]"
    # api_key assignment
    assert scrub_text("api_key='supersecretpassword123'") == "api_key=[REDACTED]"
    assert scrub_text('password: "supersecretpassword123"') == "password: [REDACTED]"


def test_scrub_google_aiza():
    # Google Gemini / AI Studio key format
    google_key = "AIzaSyD-1234567890abcdefghijklmnopqrstuv"
    res = scrub_text(f"gemini_api_key = '{google_key}'")
    assert google_key not in res
    assert "[REDACTED]" in res


def test_scrub_huggingface_token():
    hf_token = "hf_abcdefghijklmnopqrstuvwxyz0123456789"
    res = scrub_text(f"Using huggingface token {hf_token} for download")
    assert hf_token not in res
    assert "[REDACTED]" in res


def test_scrub_aws_secret_key():
    # Standard 40-char AWS secret key format
    aws_secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    res = scrub_text(f"aws_secret_access_key = '{aws_secret}'")
    assert aws_secret not in res
    assert "[REDACTED]" in res


def test_scrub_high_entropy_heuristic():
    # High-entropy mixed case + digit random secret (length >= 32)
    secret_token = "4fA9zK1mP8xQ2vL5nJ7wE0rT3yU6iO9b"
    res = scrub_text(f"token: {secret_token}")
    assert secret_token not in res
    assert "[REDACTED]" in res


def test_scrub_minimal_false_positives():
    # Ordinary code and identifiers should not be corrupted
    code_samples = [
        "def calculate_total_order_price_including_vat(items):",
        "import numpy as np",
        "url = 'https://api.github.com/repos/owner/repo/pulls'",
        "commit_hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'",
        "SELECT * FROM users WHERE status = 'active' AND created_at > now()",
        "for i in range(100): print(i)",
    ]
    for code in code_samples:
        assert scrub_text(code) == code


def test_scrub_json_recursion():
    nested = {
        "messages": [
            {"role": "user", "content": "Here is my key: sk-abcdef1234567890123456"},
            {"role": "assistant", "content": "Acknowledged"}
        ],
        "metadata": {
            "token": "ghp_12345678901234567890123456789012",
            "nested_list": ["clean", "AIzaSyD-1234567890abcdefghijklmnopqrstuv"]
        },
        "count": 42,
        "is_active": True
    }
    scrubbed = scrub_json(nested)
    assert scrubbed["count"] == 42
    assert scrubbed["is_active"] is True
    assert "sk-" not in scrubbed["messages"][0]["content"]
    assert "[REDACTED]" in scrubbed["messages"][0]["content"]
    assert "ghp_" not in scrubbed["metadata"]["token"]
    assert "[REDACTED]" in scrubbed["metadata"]["token"]
    assert "AIza" not in scrubbed["metadata"]["nested_list"][1]
    assert "[REDACTED]" in scrubbed["metadata"]["nested_list"][1]


def test_single_scrub_boundary_and_error():
    # Test that scrub_record redacts request, response_text, tool_calls, and error
    raw_record = {
        "request": {"prompt": "sk-1234567890abcdef123456"},
        "response_text": "Here is ghp_12345678901234567890123456789012",
        "tool_calls": [{"name": "test", "key": "AIzaSyD-1234567890abcdefghijklmnopqrstuv"}],
        "error": "Upstream error with leaked token: sk-9999999999abcdef999999"
    }
    scrubbed = scrub_record(raw_record)
    assert "sk-" not in scrubbed["request"]["prompt"]
    assert "[REDACTED]" in scrubbed["request"]["prompt"]
    assert "ghp_" not in scrubbed["response_text"]
    assert "[REDACTED]" in scrubbed["response_text"]
    assert "AIza" not in scrubbed["tool_calls"][0]["key"]
    assert "[REDACTED]" in scrubbed["tool_calls"][0]["key"]
    assert "sk-" not in scrubbed["error"]
    assert "[REDACTED]" in scrubbed["error"]


@pytest.mark.asyncio
async def test_log_call_error_does_not_break():
    # If pool is None or throws, log_call must swallow and not raise
    bad_rec = {
        "id": "bad-id",
        "error": "Something went wrong: sk-1234567890abcdef123456",
        "request": None,
        "response_text": None,
        "tool_calls": None
    }
    # Should complete without throwing
    await log_call(bad_rec)


def test_scrub_jwt():
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    res = scrub_text(f"Authorization: {jwt_token}")
    assert jwt_token not in res
    assert "[REDACTED]" in res


def test_scrub_database_urls():
    db_urls = [
        "postgresql://postgres_user:SuperSecretP@ssw0rd!@db.internal:5432/analytics",
        "mysql://admin:db_password_123@prod-cluster.rds.amazonaws.com:3306/main",
        "mongodb+srv://app_user:mongo_secret_pwd@cluster0.mongodb.net/prod?retryWrites=true",
        "redis://default:redis_auth_pass_xyz@cache.redis.local:6379/0"
    ]
    for url in db_urls:
        scrubbed = scrub_text(f"Connecting to DATABASE_URL={url}")
        assert url not in scrubbed
        assert "[REDACTED]" in scrubbed


def test_scrub_provider_keys():
    anthropic_key = "sk-ant-api03-abcdef1234567890abcdef1234567890"
    openrouter_key = "sk-or-v1-abcdef1234567890abcdef1234567890"

    res_ant = scrub_text(f"Using Anthropic key {anthropic_key}")
    assert anthropic_key not in res_ant
    assert "[REDACTED]" in res_ant

    res_or = scrub_text(f"Using OpenRouter key {openrouter_key}")
    assert openrouter_key not in res_or
    assert "[REDACTED]" in res_or


def test_scrub_multiline_secrets():
    multiline_text = (
        "Config block:\n"
        "DATABASE_URL=postgresql://user:pass@host:5432/dbname\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0example...\n"
        "-----END RSA PRIVATE KEY-----\n"
        "Done."
    )
    scrubbed = scrub_text(multiline_text)
    assert "user:pass@host" not in scrubbed
    assert "MIIEowIBAAKCAQEA0example" not in scrubbed
    assert "[REDACTED]" in scrubbed

