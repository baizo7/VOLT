# Project Conventions

## Coding Standards
- **Framework**: FastAPI with Pydantic v2 data models for input validation.
- **Async I/O**: `asyncpg` for PostgreSQL connection pooling and `httpx.AsyncClient` for upstream forwarding.
- **Error Handling**: The proxy must never break the client developer's tool due to capture logging errors. All persistence operations inside `log_call` are guarded and log errors to `logger.error`.
- **Structured Logging**: Standard library `logging` module configured with timestamps, log levels, and module names. No `print` statements in request or logging paths.

## API Contracts
- Endpoint paths, query parameters, header names (`X-Task-Id`, `X-Task-Type`, `X-Session-Id`, `X-Project`, `X-Observer-Token`), and `routes.json` schema must remain backward-compatible.
- Status codes:
  - `400 Bad Request`: Non-object JSON bodies or invalid JSON syntax sent to proxy routes.
  - `401 Unauthorized`: Missing or invalid token on protected endpoints when `OBSERVER_AUTH_TOKEN` is configured.
  - `422 Unprocessable Entity`: Missing required fields in `POST /outcomes` payload.
  - `502 Bad Gateway`: Upstream provider connection or protocol errors.
  - `503 Service Unavailable`: Database uninitialized or unreachable during `GET /health`.

## Testing Standards
- Unit and API tests must run without external dependencies (mock upstream providers using `httpx.MockTransport`).
- Database integration tests must be marked with `@pytest.mark.integration`.
- All tests must be executed and confirmed passing with `pytest`.
