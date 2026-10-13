import logging
import os
import re
import secrets
from typing import Any, Optional
from fastapi import Request

logger = logging.getLogger("observer.security")

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-or-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
    re.compile(r"(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp):\/\/[^\s:@'\"]+:[^\s@'\"]+@[^\s'\"/]+[^\s'\"]*"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)((?:api[_-]?key|secret|token|password|auth_token|client_secret)\s*[=:]\s*)['\"]?[^\s'\"]{8,}['\"]?"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)((?:aws_secret_access_key|aws_secret_key|secret_key|secret_access_key)\s*[=:]\s*)['\"]?[A-Za-z0-9/+=]{40}['\"]?"),
    re.compile(r"(?<![A-Za-z0-9/+=_\-])(?=[A-Za-z0-9/+=_\-]{32,})(?=[A-Za-z0-9/+=_\-]*[a-z])(?=[A-Za-z0-9/+=_\-]*[A-Z])(?=[A-Za-z0-9/+=_\-]*[0-9])[A-Za-z0-9/+=_\-]{32,}(?![A-Za-z0-9/+=_\-])"),
]


def scrub_text(s: Optional[str]) -> Optional[str]:
    """Redact known credentials and high-entropy secrets from text."""
    if not isinstance(s, str):
        return s
    for p in SECRET_PATTERNS:
        s = p.sub(lambda m: (m.group(1) if m.lastindex else "") + "[REDACTED]", s)
    return s


def scrub_json(o: Any) -> Any:
    """Recursively scrub strings within JSON data structures."""
    if isinstance(o, str):
        return scrub_text(o)
    if isinstance(o, list):
        return [scrub_json(x) for x in o]
    if isinstance(o, dict):
        return {k: scrub_json(v) for k, v in o.items()}
    return o


def scrub_record(rec: dict) -> dict:
    """Single scrubbing boundary for every persisted field."""
    if "request" in rec and rec["request"] is not None:
        rec["request"] = scrub_json(rec["request"])
    if "response_text" in rec and rec["response_text"] is not None:
        rec["response_text"] = scrub_text(rec["response_text"])
    if "tool_calls" in rec and rec["tool_calls"] is not None:
        rec["tool_calls"] = scrub_json(rec["tool_calls"])
    if "error" in rec and rec["error"] is not None:
        rec["error"] = scrub_text(str(rec["error"]))
    return rec


def check_auth(request: Request) -> bool:
    """
    Verify shared-token authentication using constant-time comparison.
    If OBSERVER_AUTH_TOKEN is unset, verifies whether REQUIRE_AUTH is strictly enforced.
    """
    token = os.environ.get("OBSERVER_AUTH_TOKEN") or os.environ.get("OBSERVER_TOKEN")
    require_auth = os.environ.get("REQUIRE_AUTH", "").lower() in ("true", "1")

    if not token:
        if require_auth:
            logger.error("Authentication required by REQUIRE_AUTH but OBSERVER_AUTH_TOKEN is unset.")
            return False
        return True

    # Candidate 1: Authorization header
    auth_header = request.headers.get("authorization", "").strip()
    if auth_header:
        parts = auth_header.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and secrets.compare_digest(parts[1], token):
            return True
        if secrets.compare_digest(auth_header, token):
            return True

    # Candidate 2: X-Observer-Token
    obs_token = request.headers.get("x-observer-token")
    if obs_token and secrets.compare_digest(obs_token, token):
        return True

    # Candidate 3: X-API-Key
    api_key = request.headers.get("x-api-key")
    if api_key and secrets.compare_digest(api_key, token):
        return True

    # Candidate 4: Query parameter (convenient for browser dashboard)
    param_token = request.query_params.get("token")
    if param_token and secrets.compare_digest(param_token, token):
        return True

    return False
