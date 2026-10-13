Yes, but in stages. Your idea is really three projects of increasing difficulty.

1. **Observer:** record what every coding model does. This is very doable.
2. **Knowledge and routing layer:** use those records to retrieve past solutions and pick the best model per task. This is also doable and gives value quickly.
3. **Your own trained model:** fine-tune an open-weight model on curated data. This is doable, but it is not the same as “inserting” other models’ data into one model.

**Two caveats:**

- **Terms of service.** Recording your own sessions for search, evaluation, and routing is generally fine. Using Claude or OpenAI outputs to train a competing model is typically prohibited in their terms, so check the current terms before you plan the training phase. Outputs from open-licensed models (DeepSeek, Nemotron, and others, depending on each license) and your own human-verified code are safer training data.
- **Expectations.** A small fine-tuned model won’t match Fable or Opus in general. Its strength is specialization: your stack, your conventions, and your codebase.

---

## Architecture pipeline

```
[Dev tools]            [Capture layer]         [Ingestion]        [Storage]
Claude CLI  ─┐         LLM gateway/proxy       Normalize to       PostgreSQL (events)
OpenCode    ─┼──────►  Tool hooks/plugins ───► common schema ───► Object store (diffs, logs)
Codex       ─┘         Git + CI hooks          + message queue    pgvector (embeddings)
                                                    │
                                                    ▼
                                       [Processing & quality]
                                       Secret/PII scrubbing → dedupe →
                                       outcome scoring → labeling
                                                    │
                      ┌─────────────────────────────┼──────────────────────────┐
                      ▼                             ▼                          ▼
              [Knowledge/RAG]                [Router + Evals]          [Training pipeline]
              Retrieve past good             Learn which model         SFT / preference tuning
              solutions for new tasks        wins per task type        of an open-weight model
                      └─────────────────────────────┼──────────────────────────┘
                                                    ▼
                                  [Your assistant / gateway + dashboard]
```

### Layer details

1. **Capture layer.** The most reliable approach is a gateway that every model call passes through, such as LiteLLM or a custom OpenAI-compatible proxy. It logs prompt, model, response, tokens, latency, and cost. Supplement it with:&#x20;
   - Hooks or plugins in the CLI tools. Claude Code and OpenCode expose events like tool use and session logs, but verify what each exposes in current docs.
   - Git hooks to capture diffs and commits.
   - CI hooks to capture build, test, lint, and security-scan results.
2. **Common event schema.** One format for all sources: `task_id, session_id, model, task_type, prompt, response, tool_calls, files_changed, build/test status, user_decision, timestamps`.
3. **Storage.** Postgres for structured records, an object store for large diffs and logs, and pgvector for embeddings.
4. **Outcome signals.** This matters most. A record is only useful for learning if you know whether it worked: tests passed, build succeeded, the user accepted or edited it, and whether the code survived in git or was reverted.
5. **Processing.** Remove secrets and PII, deduplicate, score quality, and tag by task type (UI, backend, SQL, debugging, and so on).
6. **Learning layer.**&#x20;
   - **RAG:** retrieves successful past solutions to include in new prompts.
   - **Router:** picks the model with the best measured success rate for each task type.
   - **Eval harness:** a fixed benchmark of your own tasks, so you can tell whether anything is actually improving.
   - **Fine-tuning:** SFT on verified examples, plus preference tuning (such as DPO) using accepted versus rejected pairs.
7. **Serving.** Your own gateway or assistant that uses all of the above, plus a dashboard showing model performance.
8. **Governance.** Consent, retention rules, access control, and the ability to delete records.

**Suggested stack:** Python (FastAPI) for ingestion, Postgres with pgvector, Redis or a queue, React for the dashboard, and PyTorch with Hugging Face TRL/PEFT for training.

---

## Phase-wise development plan

| Phase                         | Timeline    | Goal                                     | Deliverables                                                                                    |
| ----------------------------- | ----------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **0. Scope and rules**        | Week 1      | Decide what you may collect and for what | Data policy, list of tools to observe, task taxonomy, terms-of-service review                   |
| **1. Capture**                | Weeks 1-3   | Record everything reliably               | Gateway/proxy, CLI hooks, event schema, Postgres, basic logs                                    |
| **2. Outcomes and dashboard** | Weeks 3-5   | Know what worked                         | Git/CI integration, accept/reject tracking, React dashboard of model metrics                    |
| **3. Knowledge layer**        | Weeks 5-8   | Reuse past work                          | Scrubbing pipeline, embeddings, retrieval of similar successful solutions injected into prompts |
| **4. Evals and routing**      | Weeks 8-10  | Measure and route                        | Benchmark of 50-200 real tasks, per-task model scorecards, rule-based then learned router       |
| **5. Dataset and fine-tune**  | Weeks 10-14 | Build your own model                     | Curated JSONL, LoRA fine-tune of a small open-weight coder model, evaluation against baselines  |
| **6. Deploy and loop**        | Week 14+    | Continuous improvement                   | Serve your model behind the router, monitor, retrain periodically with regression checks        |

### Phase milestones

- **After Phase 1:** every prompt and response from your tools lands in the database.
- **After Phase 2:** you can say, for example, “Model X passes tests 70% of the time on backend tasks.”
- **After Phase 3:** a new task automatically gets relevant past solutions attached, and you can measure whether this raises the success rate.
- **After Phase 4:** the router beats any single fixed model on your benchmark.
- **After Phase 5:** your model beats its own base model on your benchmark. Matching Fable is not the bar.

---

## Key risks

- **Not enough data.** 10,000 quality records is a lot for one person or a small team, and you may only have hundreds in three months. That is fine for RAG and routing but thin for fine-tuning, so plan for synthetic and open-source data too.
- **Learning from bad outputs.** Only train on records with verified outcomes.
- **Secrets leaking into data.** Scrub API keys and credentials before storage.
- **Hidden internals.** You can see responses and tool calls, but not a model’s reasoning or weights.
- **Scope creep.** Don’t start with a new Transformer. Phases 1-4 give real value even if you never reach Phase 5.

**My recommendation:** build Phase 1 first, as a minimal proxy that logs one tool’s calls into Postgres. Once data starts flowing, the rest of the design becomes much clearer. If you’d like, I can draft the event schema and the proxy skeleton next.

yes proceed

I’ve built the Phase 1 skeleton: a capture proxy, the database schema, and a Postgres setup. I only syntax-checked `main.py` here, with no network access and no live Postgres, so I haven’t run it end to end. Expect to debug a little on first run.

**What it does**

- **Capture:** `main.py` forwards each request unchanged to the real provider and logs a scrubbed record (model, prompt, response, tool calls, latency, tokens) to Postgres. It handles streaming responses.
- **Both API styles:** it accepts the OpenAI-compatible format (OpenCode, DeepSeek, OpenRouter) and the Anthropic Messages format (Claude CLI).
- **Schema:** `schema.sql` has three tables: `tasks`, `llm_calls`, and `outcomes`. Outcomes hold build, test, lint, and accept/reject results.
- **Outcomes and stats:** `POST /outcomes` records results from CI or git hooks, and `GET /stats` shows per-model calls, latency, tokens, and pass/fail counts.
- **Routing:** `routes.json` maps a model-name prefix to an upstream URL and key, so you can add providers without touching code.
- **Safety:** common secrets are redacted before storage, and a logging failure never breaks your coding tool.

**How to run it**

1. Run `docker compose up -d` to start Postgres.
2. Install the requirements and start the proxy with `uvicorn main:app --port 8787`.
3. Point your tools at `http://localhost:8787/p/<project>/v1`. For Claude CLI, set `ANTHROPIC_BASE_URL` to `http://localhost:8787/p/<project>`.

Check each tool’s current docs for base-URL and custom-header settings. Whether a given tool can send `X-Task-Id` headers is something I couldn’t verify. If one can’t, use one task id per work session.

**Known limits**

- **Outcome attribution:** it is per task, so a task that used several models credits all of them. Phase 2 should fix this.
- **Secret scrubbing:** it is regex-based, so extend `SECRET_PATTERNS` for your own key formats and spot-check stored rows.
- **File changes:** the proxy sees model calls only, not file edits or tool executions inside the CLIs. Git and CI hooks will fill that gap in Phase 2.
- **Stored source code:** you’re storing your prompts and code, so protect the database and set a retention policy.

**First test:** route one tool, such as OpenCode with a free-tier model, through the proxy. Run a few tasks, report one outcome with the curl command from the README, then check `/stats`.

Once data is flowing, the next piece is the Phase 2 git and CI integration plus the React dashboard. I can build those next.