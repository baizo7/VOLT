"""
Configuration settings and constants for AI Model Observer.
"""
import logging
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://observer:observer@localhost:5432/observer")
ROUTES_FILE = os.environ.get("ROUTES_FILE", "routes.json")
MAX_CHARS = int(os.environ.get("MAX_STORED_CHARS", "200000"))

MAX_REQUEST_BYTES = int(os.environ.get("MAX_REQUEST_BYTES", str(15 * 1024 * 1024)))

DEFAULT_BASE = {
    "openai": "https://openrouter.ai/api/v1",
    "anthropic": "https://api.anthropic.com"
}

UPSTREAM_PATH = {
    "openai": "/chat/completions",
    "anthropic": "/v1/messages"
}

SKIP_REQ_HEADERS = {
    "host",
    "content-length",
    "connection",
    "accept-encoding",
    "transfer-encoding",
    "x-observer-token",
    "x-inject-knowledge"
}

SKIP_RESP_HEADERS = {
    "content-length",
    "content-encoding",
    "transfer-encoding",
    "connection"
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("observer")
