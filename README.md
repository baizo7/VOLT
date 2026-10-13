# AI Model Observer - Phase 1 (Capture Proxy)

A transparent, hardening capture proxy sitting between your coding tools and LLM providers. Forwards requests unchanged, scrubbed of secrets, and logs call traces, tokens, latency, errors, and outcomes into PostgreSQL.

---

## Quickstart

### 1. Start PostgreSQL
```bash
# Slices Postgres 16 (+pgvector) bound strictly to 127.0.0.1:5432 with healthchecks
docker compose up -d
```

### 2. Configure Environment
Copy `.env.example` to `.env` and adjust your credentials:
```bash
cp .env.example .env
```
Example `.env`:
```ini
POSTGRES_USER=observer
POSTGRES_PASSWORD=replace_with_secure_password
POSTGRES_DB=observer
DATABASE_URL=postgresql://observer:replace_with_secure_password@127.0.0.1:5432/observer
ROUTES_FILE=routes.json
MAX_STORED_CHARS=200000

# Optional: Shared token authentication (opt-in)
# When set, clients must supply Authorization: Bearer <token> or X-Observer-Token
OBSERVER_AUTH_TOKEN=
```

### 3. Install & Run
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --port 8787
```

---

## Configuration & Security

### Shared Token Authentication
- **Opt-in Compatibility:** When `OBSERVER_AUTH_TOKEN` is unset, authentication is disabled so existing tools continue working seamlessly.
- **Protected Endpoints:** When enabled, proxy routes (`/v1/chat/completions`, `/v1/messages`, `/p/{project}/...`), `/outcomes`, and `/stats` require a valid token.
- **Header Formats:** Clients may authenticate using:
  - `Authorization: Bearer <OBSERVER_AUTH_TOKEN>`
  - `X-Observer-Token: <OBSERVER_AUTH_TOKEN>` (recommended for proxying when tools already send provider keys in `Authorization`)
  - `X-API-Key: <OBSERVER_AUTH_TOKEN>`
- **Health Check Open:** `GET /health` remains unauthenticated for uptime monitors and container orchestrators.

### Secret Scrubbing
All persisted data (`request`, `response_text`, `tool_calls`, and `error`) passes through a single scrubbing boundary before touching PostgreSQL.
Included patterns:
- OpenAI API keys (`sk-...`)
- AWS Access Key IDs (`AKIA...`) and AWS Secret Access Keys
- GitHub Personal Access Tokens (`ghp_...`, `gho_...`, etc.)
- Google Gemini / AI Studio keys (`AIza...`)
- HuggingFace tokens (`hf_...`)
- Generic Bearer tokens & assignment patterns (`api_key`, `secret`, `password`)
- PEM private keys (`-----BEGIN ... PRIVATE KEY-----`)
- Generic high-entropy random secrets (mixed-case alphanumeric tokens >= 32 characters)

### Database Hardening & Network Isolation
- PostgreSQL is bound exclusively to `127.0.0.1:5432` in `docker-compose.yml`, preventing external network exposure.
- Credentials are read directly from the environment (`${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`) with no default weak credentials committed in compose.
- Built-in Docker healthcheck validates database readiness via `pg_isready`.

### Data Retention & Privacy
Because LLM capture stores code snippets and prompts, consider implementing a data retention policy:
- **Periodic Pruning:** Execute a cleanup query or cron job to drop records older than your organization's retention window (e.g. 30 or 90 days):
  ```sql
  DELETE FROM outcomes WHERE created_at < NOW() - INTERVAL '90 days';
  DELETE FROM llm_calls WHERE ts < NOW() - INTERVAL '90 days';
  DELETE FROM tasks WHERE created_at < NOW() - INTERVAL '90 days'
    AND task_id NOT IN (SELECT DISTINCT task_id FROM llm_calls);
  ```
- **Storage Limits:** Long response bodies and streaming buffers are capped in memory and storage by `MAX_STORED_CHARS` (default: 200,000 characters).

---

## Point Your Tools At The Proxy

- **OpenAI-Compatible Tools (OpenCode, Codex, DeepSeek, OpenRouter):**
  Set the base URL to `http://localhost:8787/p/<project>/v1` (or `http://localhost:8787/v1`).
- **Claude CLI / Anthropic:**
  Set `ANTHROPIC_BASE_URL=http://localhost:8787/p/<project>`. Upstream Anthropic calls resolve to `/messages`.
- **Session & Task Headers:**
  Add optional tracking headers: `X-Task-Id`, `X-Task-Type`, `X-Session-Id`, `X-Project`.
  If authentication is enabled, include `X-Observer-Token: <token>`.

---

## Outcomes & Analytics API

### Report Outcomes (`POST /outcomes`)
Report build, test, lint, or feedback results for a task. Requires valid JSON with `task_id`, `kind`, and `status`:
```bash
curl -X POST http://localhost:8787/outcomes \
  -H "Content-Type: application/json" \
  -H "X-Observer-Token: $OBSERVER_AUTH_TOKEN" \
  -d '{"task_id":"task_1024","kind":"test","status":"pass","details":{"passed":48,"failed":2}}'
```

### View Performance Stats (`GET /stats`)
Returns per-model metrics: call counts, average latency, token counts, and passes/fails. Multi-model tasks attribute outcomes to the most recent model used (last-touch attribution), avoiding double-counting:
```bash
curl http://localhost:8787/stats -H "Authorization: Bearer $OBSERVER_AUTH_TOKEN"
```

### Health Readiness (`GET /health`)
Database-aware readiness probe:
- Returns `200 {"ok": true, "status": "ready"}` when the database pool is connected and responsive.
- Returns `503 {"ok": false, "status": "unready"}` if PostgreSQL is down or unreachable.

### Interactive Dashboard (`GET /dashboard` or `GET /`)
An interactive, auto-refreshing analytics dashboard providing:
- Real-time service and database health indicators.
- Per-model leaderboard with call volume, average latency, tokens, pass/fail counts, and success rates.
- Recent tasks table with outcome status badges and primary model attribution.
- Point your browser to `http://localhost:8787/dashboard` (or `http://localhost:8787/?token=<token>` if authentication is enabled).

### Task Audit & Trace API (`GET /tasks` & `GET /tasks/{task_id}`)
- `GET /tasks?limit=50`: List recent tasks with primary model, call counts, and latest outcome.
- `GET /tasks/{task_id}`: Retrieve the full audit trail for a task, including all proxied LLM calls and recorded outcomes.

### Retention Pruning (`POST /admin/prune`)
Trigger automated retention policy cleanup via API:
```bash
curl -X POST "http://localhost:8787/admin/prune?days=90" \
  -H "X-Observer-Token: $OBSERVER_AUTH_TOKEN"
```

---

## Phase 2: Hooks & Automation

### Automated Git Commit Tracking
Capture commits, branches, and files changed when code is accepted:
1. **Install Git Hook**:
   ```bash
   python -m hooks.install_hooks
   ```
2. **Commit with Task ID**:
   Prefix or tag your commit message with `[task_123]` or set `OBSERVER_TASK_ID=task_123`:
   ```bash
   git commit -m "[task_1024] Refactored authentication and added unit tests"
   ```
   The `post-commit` hook automatically notifies the Observer with status `accepted` and diff metadata.

### Automated CI / Test Runner Reporter
Wrap test, lint, or build commands in your CI pipeline or local scripts to report outcomes automatically:
```bash
python -m hooks.ci_reporter --task-id task_1024 --kind test -- pytest
```
- Executes the test suite and streams stdout live.
- Parses test summary metrics (`passed`, `failed`, `skipped`).
- Posts the outcome record to `/outcomes`.
- Exits with the command's original exit code so CI status is preserved.

---

## Phase 3: Solution Knowledge & Semantic Retrieval (pgvector)

Store verified successful solutions and retrieve them via semantic similarity (using PostgreSQL `pgvector` with HNSW indexing) to augment developer prompts.

### 1. Index Verified Solution (`POST /knowledge/solutions`)
```bash
curl -X POST http://localhost:8787/knowledge/solutions \
  -H "Content-Type: application/json" \
  -H "X-Observer-Token: $OBSERVER_AUTH_TOKEN" \
  -d '{
    "task_id": "task_1024",
    "problem_summary": "Fix SSE streaming chunk truncation",
    "solution_code": "async def stream(): ...",
    "task_type": "proxy",
    "outcome_status": "pass",
    "embedding": [0.012, -0.043, ...]
  }'
```

### 2. Semantic Search (`POST /knowledge/search`)
Query by embedding vector (cosine similarity) or keyword text fallback:
```bash
# Query by embedding vector
curl -X POST http://localhost:8787/knowledge/search \
  -H "Content-Type: application/json" \
  -H "X-Observer-Token: $OBSERVER_AUTH_TOKEN" \
  -d '{"query_embedding": [0.012, -0.043, ...], "limit": 5, "task_type": "proxy"}'

### 3. Automatic Prompt Augmentation (RAG Middleware)
To automatically retrieve relevant past solutions and attach them to your developer tool's prompt context, supply the header:
```http
X-Inject-Knowledge: true
```
(Or set `AUTO_INJECT_KNOWLEDGE=1` in your `.env` to enable it globally).
When enabled, the proxy extracts your latest prompt, performs vector similarity search across past verified solutions, and transparently injects top matches into the system prompt before forwarding upstream.

### 4. Continuous Auto-Indexing
Whenever a task passes verification (`POST /outcomes` with `status: "pass"` or `"accepted"`), the Observer automatically extracts the task's user prompt and generated code, computes embeddings, and indexes the solution into `pgvector` for future reuse.

---

## Phase 4: Intelligent Model Router & Benchmark Suite

### 1. Intelligent Model Router (`app/router.py`)
Routes requests dynamically to the highest-performing model based on historical telemetry and verified pass rates.

- **Dynamic Model Selection**: Set `model: "auto"` or `model: "auto:<task_type>"` in your client request payload, or supply the `X-Route-Strategy` header:
  - `best_pass_rate` (default): Selects model with highest verified pass rate using Laplace smoothing confidence.
  - `lowest_latency`: Selects model with lowest average latency.
  - `balanced`: Balances pass rate against latency penalty.
- **Latency Constraints**: Supply `X-Max-Latency-Ms: 1000` to exclude models exceeding response time bounds.
- **Audit Response Headers**: The proxy returns `X-Observer-Routed-Model` and `X-Observer-Route-Strategy` headers to inform callers of routing decisions.
- **Recommendations API (`GET /router/recommendations`)**:
  ```bash
  curl http://localhost:8787/router/recommendations \
    -H "Authorization: Bearer $OBSERVER_AUTH_TOKEN"
  ```

### 2. Evaluation Benchmark Suite (`benchmarks/`)
Standardized evaluation framework measuring model code generation quality on verified tasks:
- **Tasks (`benchmarks/tasks.py`)**: Standard programming benchmarks covering algorithms, data structures, and string parsing.
- **Runner (`benchmarks/runner.py`)**: Executes tasks through the Observer proxy, runs unit tests in sandboxed namespaces, and posts verified outcomes to `/outcomes`.
- **Reporter (`benchmarks/eval_reporter.py`)**: Generates Markdown leaderboards comparing pass rates, latencies, and errors across models.

---

## Phase 5: Dataset Curation & LoRA Fine-Tuning Pipeline

Build custom specialized coder models fine-tuned on verified, scrubbed telemetry captured across your development stack.

### 1. Dataset Export API (`POST /admin/export-dataset`)
Export curated datasets with automatic train/validation splitting:
```bash
# Export Supervised Fine-Tuning (SFT) multi-turn conversations
curl -X POST http://localhost:8787/admin/export-dataset \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OBSERVER_AUTH_TOKEN" \
  -d '{"dataset_type": "sft", "val_split": 0.1, "limit": 1000}'

# Export Direct Preference Optimization (DPO) chosen vs rejected pairs
curl -X POST http://localhost:8787/admin/export-dataset \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OBSERVER_AUTH_TOKEN" \
  -d '{"dataset_type": "dpo", "val_split": 0.1, "limit": 1000}'
```

### 2. Dataset Quality Statistics (`GET /admin/dataset/stats`)
```bash
curl http://localhost:8787/admin/dataset/stats \
  -H "Authorization: Bearer $OBSERVER_AUTH_TOKEN"
```

### 3. LoRA Fine-Tuning Runner (`training/train_lora.py`)
Fine-tune open-weight coding models (e.g. DeepSeek-Coder, Qwen2.5-Coder) using PEFT/LoRA:
```bash
# Dry-run validation (checks dataset formatting without GPU requirements)
python -m training.train_lora --dataset ./data/train_sft.jsonl --output ./checkpoints/my_adapter --dry-run

# Full GPU LoRA fine-tuning
python -m training.train_lora --dataset ./data/train_sft.jsonl --output ./checkpoints/my_adapter
```

### 4. Regression & Win-Rate Evaluation (`training/evaluate_finetuned.py`)
Compares the fine-tuned adapter against the base model on standardized benchmark tasks to verify improvements and prevent regressions.

---

## Testing

Run the test suite with pytest:

```bash
# Run full unit & API test suite (107 tests passing, ~0.8s)
pytest

# Run live pgvector integration tests against PostgreSQL
docker compose up -d
pytest -m integration

# Run benchmark and training tests
pytest tests/test_benchmarks.py tests/test_training.py tests/test_dataset.py
```



