-- AI Model Observer: Phase 1 schema (PostgreSQL 14+)

CREATE TABLE IF NOT EXISTS tasks (
    task_id     TEXT PRIMARY KEY,
    project     TEXT,
    task_type   TEXT,            -- e.g. frontend_generation, debugging, sql
    title       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per model call that passes through the proxy
CREATE TABLE IF NOT EXISTS llm_calls (
    id             UUID PRIMARY KEY,
    ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
    project        TEXT,
    task_id        TEXT REFERENCES tasks(task_id),
    session_id     TEXT,
    task_type      TEXT,
    model          TEXT NOT NULL,
    upstream       TEXT NOT NULL,         -- base URL the call was forwarded to
    api_style      TEXT NOT NULL,         -- 'openai' | 'anthropic'
    streamed       BOOLEAN NOT NULL,
    request        JSONB,                 -- scrubbed request body
    response_text  TEXT,                  -- scrubbed assistant text
    tool_calls     JSONB,                 -- tool calls the model asked for (best effort)
    status_code    INT,
    latency_ms     INT,
    input_tokens   INT,
    output_tokens  INT,
    error          TEXT
);
CREATE INDEX IF NOT EXISTS llm_calls_task_idx  ON llm_calls (task_id);
CREATE INDEX IF NOT EXISTS llm_calls_model_idx ON llm_calls (model, ts DESC);

-- Outcome signals: build/test/lint results, user accept/reject, etc.
CREATE TABLE IF NOT EXISTS outcomes (
    id          BIGSERIAL PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id),
    kind        TEXT NOT NULL,            -- build | test | lint | security | user_feedback | git
    status      TEXT NOT NULL,            -- pass | fail | accepted | rejected | edited
    details     JSONB,                    -- e.g. {"passed":48,"failed":2}
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS outcomes_task_idx ON outcomes (task_id);

-- Phase 3: pgvector extension & solution knowledge store
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS solutions (
    id              BIGSERIAL PRIMARY KEY,
    task_id         TEXT REFERENCES tasks(task_id) ON DELETE CASCADE,
    task_type       TEXT,
    project         TEXT,
    problem_summary TEXT NOT NULL,
    solution_code   TEXT NOT NULL,
    outcome_status  TEXT NOT NULL,        -- 'pass' | 'accepted'
    embedding       vector(1536),         -- vector embeddings for similarity search
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS solutions_task_idx ON solutions (task_id);
CREATE INDEX IF NOT EXISTS solutions_embedding_idx ON solutions USING hnsw (embedding vector_cosine_ops);

