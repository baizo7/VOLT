# ⚡ VOLT-AI

**Intelligent Multi-Model AI Coordination, Routing & Observability Engine**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-159%20Passed-brightgreen.svg)]()
[![Cloud Deployment](https://img.shields.io/badge/Render-Live%20Ready-46E3B7.svg)](https://volt-ai-lmgz.onrender.com)

VOLT-AI is a high-performance multi-model coordination, dynamic routing, and observability platform that sits between developer tools and LLM providers. It forwards requests with zero overhead, scrubs all secrets in flight, logs end-to-end telemetry into PostgreSQL, and coordinates multi-model synthesis across Gemini, Claude, DeepSeek, OpenRouter, and local models.

---

## 🚀 Key Capabilities

- **🧠 Multi-Model Coordination Engine (`VOLT-AI` / `volt-ai-1.0`)**
  Routes requests through specialized pipelines (`code`, `general`, `fast`, `creative`) with automated fallback tiers.
- **💻 Interactive Developer CLI (`volt` & `volt-coder`)**
  Generate code directly from your terminal (`volt-coder code "..."`), launch multi-turn interactive sessions (`volt-coder chat`), inspect provider models, and monitor token consumption.
- **🔌 Universal Drop-in Proxy (OpenAI & Anthropic Compatible)**
  Intercepts and instruments traffic transparently at `/v1/chat/completions`, `/v1/messages`, and `/v1/models`. Drop-in ready for Cursor, Aider, OpenCode, Cline, Continue.dev, and native SDKs.
- **📊 Real-Time Observability Dashboard (`/dashboard`)**
  Glassmorphic UI showing live call streams, latency, token spend, model leaderboards, test pass rates, and developer onboarding snippets.
- **🛡️ Zero-Leak Secret Scrubbing**
  Automated detection and redaction of 7+ secret classes (OpenAI, AWS, GitHub, Google AI Studio, Anthropic, PEM keys, and high-entropy tokens) before persistence.
- **🔍 Semantic Knowledge Engine (`pgvector`)**
  Caches verified code solutions and uses cosine similarity to automatically augment prompts with past successful solutions (RAG middleware).
- **🎯 Dataset Export & LoRA Fine-Tuning**
  Exports scrubbed, verified task telemetry into SFT and DPO formats to train local open-weight models (DeepSeek-Coder, Qwen2.5-Coder) with PEFT/LoRA.
- **☁️ Cloud & Local Deployments**
  Ready for single-click deployment via Render (`render.yaml`) and local development via Docker Compose.

---

## 📐 System Architecture

```
                                  ┌─────────────────────────────┐
                                  │   Developer IDEs & Tools    │
                                  │ (Cursor, Aider, CLI, SDKs)  │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │             ⚡ VOLT-AI Core Engine               │
                        │                                                 │
                        │  • Secret Scrubbing Boundary (Zero-Leak)        │
                        │  • RBAC & Token Authentication                  │
                        │  • Multi-Model Coordinator & Dynamic Router     │
                        │  • pgvector Semantic RAG Injector               │
                        └──────────────┬───────────────────┬──────────────┘
                                       │                   │
                  ┌────────────────────┴─────┐             │
                  ▼                          ▼             ▼
       ┌─────────────────────┐    ┌─────────────────────┐  ┌─────────────────────┐
       │   Public Providers  │    │  Local / Edge LLMs  │  │   PostgreSQL + RAG  │
       │ (Gemini, Anthropic, │    │ (Ollama, vLLM,      │  │ (Telemetry, Spans,  │
       │  DeepSeek, Router)  │    │  Localhost :8080)   │  │  pgvector vectors)  │
       └─────────────────────┘    └─────────────────────┘  └─────────────────────┘
```

---

## ⚡ Quickstart

### Option 1: Use the Live Cloud Server

The central VOLT-AI engine is live at:
```text
https://volt-ai-lmgz.onrender.com
```

Connect your terminal immediately:
```bash
# Configure CLI to point to cloud VOLT-AI
python volt.py activate --server https://volt-ai-lmgz.onrender.com

# Start coding
python volt-coder.py "Write a Python script to parse JSON streams"
```

---

### Option 2: Run Locally (Docker Compose + Python)

#### 1. Start PostgreSQL with `pgvector`
```bash
docker compose up -d
```

#### 2. Configure Environment
```bash
cp .env.example .env
```

Ensure your `.env` contains:
```ini
POSTGRES_USER=observer
POSTGRES_PASSWORD=observer_secret_pw_123
POSTGRES_DB=observer
DATABASE_URL=postgresql://observer:observer_secret_pw_123@127.0.0.1:5432/observer
ROUTES_FILE=routes.json
MAX_STORED_CHARS=200000

# Security (Optional shared token & Admin Key)
VOLT_ADMIN_KEY=your_admin_secret_key

# Provider Keys (Fallback / Upstream routing)
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_key
DEEPSEEK_API_KEY=your_deepseek_key
```

#### 3. Start the Server
```bash
# Using Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8787 --reload
```

Or using the automated PowerShell runner:
```powershell
.\start-volt.ps1
```

Visit the interactive dashboard at **`http://localhost:8787/dashboard`**.

---

## 💻 Developer CLI (`volt-coder` & `volt`)

VOLT-AI includes standalone developer CLI utilities located in `cli/main.py`:

| Command | Description |
| :--- | :--- |
| `volt-coder "prompt"` | Run single-turn code generation with automatic multi-model fallback |
| `volt-coder chat` | Launch an interactive multi-turn terminal session |
| `volt-coder code -f file.py "task"` | Pass existing files into context for synthesis/refactoring |
| `volt-coder models` | Display active specialist roster, licenses, and tracks |
| `volt usage` | Display your personal token consumption, calls, and latency |
| `volt usage --all` | Display organization-wide metrics (requires `VOLT_ADMIN_KEY`) |
| `volt dashboard` | Open the web analytics dashboard in your default browser |
| `volt activate` | Interactively configure and authenticate your local terminal |

### Examples

```bash
# Quick code generation
python volt-coder.py "Write a binary search algorithm in Rust"

# Code refactoring with file context
python volt-coder.py code -f app/security.py "Review this file for potential timing attacks"

# Interactive coding session
python volt-coder.py chat

# Check coordination roster
python volt-coder.py models
```

---

## 🔌 Tool Integration (Drop-in Proxy)

Route your favorite coding tools through VOLT-AI by redirecting their base URL:

### 1. OpenAI SDK / Universal Tools (Cursor, OpenCode, Aider)
```bash
# Point to local VOLT-AI
export OPENAI_BASE_URL="http://localhost:8787/v1"
export OPENAI_API_KEY="volt-local"

# Or point to Cloud VOLT-AI
export OPENAI_BASE_URL="https://volt-ai-lmgz.onrender.com/v1"
export OPENAI_API_KEY="volt-cloud"
```

In PowerShell:
```powershell
$env:OPENAI_BASE_URL = "https://volt-ai-lmgz.onrender.com/v1"
$env:OPENAI_API_KEY  = "volt-cloud"
```

### 2. Anthropic SDK / Claude CLI
```bash
export ANTHROPIC_BASE_URL="https://volt-ai-lmgz.onrender.com"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 3. Tracking Headers
Enhance telemetry by attaching contextual headers to requests:
- `X-Session-Id`: Developer or terminal username
- `X-Task-Id`: Active tracking ID (e.g. `task_1042`)
- `X-Project`: Active repository or project name
- `X-Inject-Knowledge: true`: Enable automatic semantic RAG injection

---

## 📡 API Reference

### Proxy Endpoints
- `POST /v1/chat/completions`: OpenAI-compatible completion proxy.
- `POST /v1/messages`: Anthropic-compatible messages proxy.
- `GET /v1/models`: Model roster list (`VOLT-AI`, `volt-ai-1.0`, provider endpoints).

### Telemetry & Outcomes
- `POST /outcomes`: Record test, build, lint, or human feedback outcomes for tasks.
  ```json
  {
    "task_id": "task_42",
    "kind": "test",
    "status": "pass",
    "details": { "passed": 159, "failed": 0 }
  }
  ```
- `GET /stats`: Retrieve model leaderboard, token metrics, latency, and success rates.
- `GET /tasks`: List recent task sessions and last-touch model attribution.
- `GET /tasks/{task_id}`: Inspect full trace history and telemetry for a specific task.

### Knowledge Engine (pgvector)
- `POST /knowledge/solutions`: Index verified code solutions.
- `POST /knowledge/search`: Vector cosine similarity search across solutions.

### Administration & Datasets
- `POST /admin/export-dataset`: Export captured telemetry into `sft` or `dpo` format.
- `POST /admin/prune?days=90`: Prune telemetry records older than retention threshold.
- `POST /admin/verify`: Validate admin key credentials.

---

## 🔒 Security & Secret Redaction

Every request, response body, streaming chunk, and tool call passes through an in-memory secret scrubbing boundary before reaching PostgreSQL:

- **OpenAI Keys**: `sk-[a-zA-Z0-9]{20,}`
- **AWS Credentials**: `AKIA[0-9A-Z]{16}` and secret access keys
- **GitHub Personal Access Tokens**: `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`
- **Google AI / Gemini Keys**: `AIza[0-9A-Za-z-_]{35}`
- **Anthropic Keys**: `sk-ant-[a-zA-Z0-9_-]+`
- **Private Keys**: `-----BEGIN ... PRIVATE KEY-----`
- **High-Entropy Tokens**: Mixed-case alphanumeric strings $\ge 32$ characters

---

## 🧪 Testing

VOLT-AI includes an automated test suite covering proxy routing, coordination, token authentication, secret redaction, and CLI workflows:

```bash
# Run unit & API test suite (159 passing)
pytest -m "not integration"

# Run with coverage report
pytest --cov=app --cov=cli

# Run live pgvector integration tests (requires Docker PostgreSQL)
docker compose up -d
pytest -m integration
```

---

## ☁️ Cloud Deployment (Render)

VOLT-AI includes a production-ready Render Blueprint specification:

1. Push your repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New > Blueprint**.
3. Select your repository. Render automatically reads [render.yaml](file:///D:/projects/VOLT/render.yaml).
4. Set your environment variables (`DATABASE_URL`, `VOLT_ADMIN_KEY`, `GEMINI_API_KEY`).
5. Deploy!

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
