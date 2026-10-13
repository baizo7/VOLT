# Project Roadmap

## Phase 1: Hardened Capture Proxy (Current - Completed)
- [x] Transparent proxy for OpenAI and Anthropic API styles
- [x] PostgreSQL persistence with schema auto-application
- [x] Single scrubbing boundary redacting all persisted fields (including `error`)
- [x] Extended secret detection (Google AIza, HuggingFace, AWS secret key, high-entropy tokens)
- [x] Opt-in shared-token authentication
- [x] Database network isolation to `127.0.0.1` and credential extraction
- [x] Input validation on proxy bodies and `/outcomes`
- [x] Bounded streaming capture buffer in memory
- [x] Streaming tool-calls reconstruction for OpenAI and Anthropic
- [x] Database-aware `/health` readiness check
- [x] Last-touch outcome attribution in `/stats`
- [x] Full test suite (unit, API, and PostgreSQL integration tests)

## Phase 2: Tool Events, CLI Hooks & Dashboard (Completed)
- [x] Automated git commit and branch tracking hooks (`hooks/git_tracker.py`, `hooks/install_hooks.py`)
- [x] CI/CD integration plugins for automated outcome reporting (`hooks/ci_reporter.py`)
- [x] Web analytics dashboard for real-time visualization (`GET /dashboard`, `GET /`)
- [x] Task audit trail API (`GET /tasks`, `GET /tasks/{task_id}`)
- [x] Data retention and automatic pruning service (`POST /admin/prune`)
- [x] Decompose `main.py` into modular packages (`app/config`, `app/routing`, `app/security`, `app/parsing`, `app/storage`, `app/dashboard`)

## Phase 3: Solution Knowledge Layer & pgvector Semantic Retrieval (Completed)
- [x] Enable PostgreSQL `vector` extension and `solutions` table with HNSW index
- [x] Solution indexing API (`POST /knowledge/solutions`, `app/knowledge.py`)
- [x] Semantic similarity retrieval using cosine distance `<=>` (`POST /knowledge/search`)
- [x] Embedding generation pipeline with offline fallback (`app/embeddings.py`)
- [x] Prompt injection middleware augmenting developer prompts (`app/rag.py`, `X-Inject-Knowledge`)
- [x] Continuous auto-indexing of verified passing solutions upon outcome reporting
- [x] Automated unit, API, and live pgvector integration tests (`tests/test_embeddings.py`, `tests/test_rag.py`)

## Phase 4: Evals and Intelligent Model Router (Completed)
- [x] Standardized coding benchmark evaluation harness (`benchmarks/tasks.py`, `benchmarks/runner.py`)
- [x] Dynamic model router selecting highest pass-rate model based on verified telemetry (`app/router.py`)
- [x] Latency and balanced constraint routing policies (`X-Max-Latency-Ms`, `X-Route-Strategy`, `model: "auto"`)
- [x] Recommendations API endpoint (`GET /router/recommendations`)
- [x] Benchmark Markdown and leaderboard report generation (`benchmarks/eval_reporter.py`)
- [x] Full test coverage with automated unit and mock tests (`tests/test_router.py`, `tests/test_benchmarks.py`)

## Phase 5: Dataset Curation & Model Fine-Tuning Pipeline (Completed)
- [x] Automated SFT dataset curation engine from verified passing tasks (`app/dataset.py`)
- [x] Direct Preference Optimization (DPO) pairwise dataset exporter for preference tuning (`app/dataset.py`)
- [x] Dataset export and quality statistics API endpoints (`POST /admin/export-dataset`, `GET /admin/dataset/stats`)
- [x] LoRA / PEFT hyperparameter configuration framework (`training/lora_config.py`)
- [x] Supervised fine-tuning execution script with dry-run CI validation (`training/train_lora.py`)
- [x] Base vs Fine-Tuned regression benchmark comparison and report generator (`training/evaluate_finetuned.py`)
- [x] Automated unit and integration tests covering dataset curation and training (`tests/test_dataset.py`, `tests/test_training.py`)

## Phase 6: Continuous Deployment & Retraining Loop (Next)
- [ ] Automated scheduled retraining triggers on telemetry thresholds (e.g., after 500 new verified tasks)
- [ ] Continuous adapter serving behind router with fallback to upstream providers




