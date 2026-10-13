# Architectural Decisions

## ADR-001: Monolith Architecture for Phase 1
- **Status**: Accepted
- **Context**: Phase 1 requires a minimal, high-performance capture proxy.
- **Decision**: Keep proxy routing, parsing, scrubbing, and persistence in `main.py` for Phase 1 while clearly delineating functional boundaries. Defer multi-module decomposition until Phase 2.

## ADR-002: Single Scrubbing Boundary
- **Status**: Accepted
- **Context**: Previously, secret scrubbing was scattered and error messages were saved unscrubbed, potentially leaking secrets echoed by upstream APIs.
- **Decision**: Centralize all data sanitization in `scrub_record()`. All stored fields (`request`, `response_text`, `tool_calls`, `error`) must pass through this single boundary before database insertion.

## ADR-003: Opt-in Shared Token Authentication
- **Status**: Accepted
- **Context**: The proxy and reporting APIs must be protected from unauthorized access, but existing developer setups must not break unexpectedly.
- **Decision**: Support shared-token authentication via `OBSERVER_AUTH_TOKEN`. If unset, auth is disabled for backward compatibility. Protects proxy endpoints, `/outcomes`, and `/stats`; leaves `/health` unauthenticated.

## ADR-004: Last-Touch Attribution for Multi-Model Tasks
- **Status**: Accepted
- **Context**: A task might invoke multiple models during iteration. Crediting all models for a single outcome caused double-counting in `/stats`.
- **Decision**: Attribute the outcome to the most recent model called for that `task_id` (`DISTINCT ON (task_id) ... ORDER BY task_id, ts DESC`). Single-model task metrics remain unchanged.

## ADR-005: Bounded Streaming Capture
- **Status**: Accepted
- **Context**: Streaming responses were buffered entirely in memory before join and length truncation, allowing unbounded memory consumption on large generations.
- **Decision**: Cap the in-memory capture buffer during streaming iteration at `MAX_STORED_CHARS` while streaming the complete raw payload to the client.
