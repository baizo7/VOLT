# Architecture Overview

## System Purpose
The AI Model Observer sits between developer tools (OpenCode, Claude CLI, custom IDE extensions) and upstream LLM providers (OpenAI, Anthropic, OpenRouter, DeepSeek). It intercepts request and response streams, scrubs confidential information, persists telemetry and audit records to PostgreSQL, and aggregates task performance outcomes.

## Modular Architecture Packages (`app/`)
- **`app/config.py`**: Configuration constants, environment resolution, and logging setup.
- **`app/security.py`**: Centralized secret scrubbing boundary (`scrub_record`, `scrub_text`, `scrub_json`) and shared token authentication.
- **`app/routing.py`**: Route resolution and dynamic mapping to upstream LLM providers.
- **`app/parsing.py`**: Resilient SSE and non-streaming response parsers for OpenAI delta and Anthropic tool use structures.
- **`app/storage.py`**: PostgreSQL database pool lifecycle, queries for metrics, task traces, and retention pruning.
- **`app/dashboard.py`**: Real-time web analytics dashboard UI.
- **`app/knowledge.py`**: Phase 3 semantic solution indexing and pgvector HNSW similarity search.
- **`hooks/git_tracker.py`**: Phase 2 git post-commit hook capturing branch, commit metadata, and changed files.
- **`hooks/ci_reporter.py`**: Phase 2 universal test runner wrapper capturing exit codes, metrics, and posting outcome signals.
- **`main.py`**: Reverse proxy entrypoint orchestrating modules with 100% backward-compatible API and test surfaces.

