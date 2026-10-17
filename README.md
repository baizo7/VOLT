# ⚡ VOLT-AI

**Autonomous Multi-Model AI Coordination, Routing & Observability Engine**

[![PyPI Version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/volt-ai/)
[![Author: Baizo](https://img.shields.io/badge/Author-Baizo%20%28S%20Sanjai%29-blue.svg)](https://github.com/baizo7)
[![Model License: Apache 2.0](https://img.shields.io/badge/Model%20License-Apache%202.0%20%28Open%20Source%29-green.svg)](LICENSE)
[![Platform License: Proprietary](https://img.shields.io/badge/Platform%20License-Proprietary%20%2F%20Source--Available-red.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-179%20passed%20%28100%25%29-brightgreen.svg)]()
[![Cloud Endpoint](https://img.shields.io/badge/Render-Live%20Endpoint-46E3B7.svg)](https://volt-ai-lmgz.onrender.com)
[![BYOK Architecture](https://img.shields.io/badge/Access-Bring--Your--Own--Key%20%28BYOK%29-orange.svg)]()

---

> ### ⚠️ Intellectual Property & Licensing Notice
> **The VOLT-AI Model (`volt-ai-1.0` specifications, weights, and inference schema) is released as Open Source under the Apache License 2.0.**
>
> The **VOLT-AI Platform, Core Coordination Engine, Dynamic Multi-Model Router, Secret Scrubbing Pipeline, and Observability Backend** are proprietary intellectual property created by **S Sanjai (Baizo)**. All platform rights are strictly reserved. Commercial redistribution, unauthorized resale, or hosting of competing SaaS proxy services without express prior written permission is prohibited. See [LICENSE](LICENSE) for full legal terms and credits.

---

## 🌟 Overview

VOLT-AI provides autonomous multi-model coordination, dynamic specialist fallback, real-time observability, and a community developer portal:

- **1-Command Global Install**: `pip install volt-ai` gives immediate terminal access with zero heavy dependencies.
- **Free Community Tier (Zero Setup Required)**: Anyone can start coding immediately with `VOLT-AI` without an API key (up to 30 free daily requests).
- **Google Authentication & Web Developer Portal**: Visit [volt-ai-lmgz.onrender.com/login](https://volt-ai-lmgz.onrender.com/login) to sign in with Google or instant developer demo, manage your profile, and generate a personal `volt_live_...` API key with 50 free requests per day.
- **Bring-Your-Own-Key (BYOK) for Unlimited Power**: Provide your personal provider key (OpenRouter, DeepSeek, Gemini, or OpenAI) for 100% unlimited requests billed to your provider at zero markup.
- **Multi-Model Specialist Roster**: Automatically routes requests across 5 dedicated open-weight specialists:
  - ⚡ **Fast Coder**: Quick code generation and syntax repair (`Qwen2.5-Coder-1.5B` / `32B`).
  - 🧠 **Deep Reasoner**: Step-by-step chain-of-thought, architectural planning, and algorithm design (`DeepSeek-R1`).
  - 🏗️ **Heavy Coder**: Large-scale refactoring, systems engineering, and multi-file codebases (`Qwen2.5-Coder-32B`).
  - 📐 **Math Specialist**: Numerical proofs, matrix operations, and mathematical reasoning (`Qwen2.5-Math-7B`).
  - 👁️ **Vision Specialist**: UI mockup analysis, screenshot-to-code, and visual inspection (`Qwen2-VL-7B`).
- **Two-Pass Reasoning Pipeline**: When complex architectural tasks are detected, the reasoning specialist designs a verified blueprint first, which the coding specialist then turns into modular, production-ready code.
- **Burst Rate Limiting**: Built-in SlowAPI protection with tier-aware quotas (10 req/min for unauthenticated community IPs; 30 req/min for portal keys; 120 req/min for BYOK) and Cloudflare `CF-Connecting-IP` support.
- **Universal Drop-in Proxy**: OpenAI & Anthropic API compatible proxy supporting Cursor, Aider, OpenCode, VS Code extensions, and native SDKs.
- **Zero-Leak Secret Redaction**: In-flight regex redaction strips API keys, AWS credentials, GitHub tokens, and private keys before PostgreSQL persistence.
- **Live Observability Dashboard**: Real-time glassmorphism analytics dashboard tracking tokens, latency, cost, and test pass rates.

---

## 🔑 3 Ways to Access VOLT-AI

| Tier | API Key Required? | Quota / Limits | Rate Limit | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **1. Free Starter** | ❌ None | **30 free requests / day** | 10 req / min per IP | Instant testing, quick CLI queries, casual terminal scripting |
| **2. Portal Developer Key** | ⚡ `volt_live_...` (1-Click Generate) | **50 free requests / day** | 30 req / min | Personal developer projects, VS Code / Cursor plugins, scripts |
| **3. BYOK (Bring Your Own Key)** | 🔑 OpenRouter, DeepSeek, Gemini, OpenAI | ♾️ **Unlimited** | 120 req / min | Power users, large codebases, continuous development |

---

## 🚀 Quickstart: Install via PyPI

Install the lightweight, zero-dependency CLI on any system (Windows, macOS, Linux):

```bash
pip install volt-ai
```

### 1. Test Connectivity
```bash
volt test
```
*Expected output: `[+] Success! Response from VOLT-AI: 'PONG'`*

### 2. Generate Code Immediately (Free Community Tier)
```bash
# Generate single-pass code
volt code "Write a fast thread-safe LRU cache in Python"

# Auto-write generated code blocks directly to files
volt code -w "Create a modern responsive Tailwind landing page with a hero and pricing grid"
```

### 3. Inspect Specialist Catalog
```bash
volt models
```

---

## 🛠️ Developer Setup & Terminal Activation

Configure your terminal to route through the central VOLT-AI server or attach your personal provider key for unlimited requests:

### Activate VOLT-AI
```bash
volt activate
```
This interactive prompt configures:
1. **Central Server URL** (default: `https://volt-ai-lmgz.onrender.com`)
2. **Developer Username / Session ID**
3. **Default Project Name**
4. **Provider API Key (Optional)**: OpenRouter, DeepSeek, Google Gemini, or OpenAI key for unlimited BYOK quota.

Configuration is saved locally to `~/.volt-ai/config.json`.

---

## 💻 CLI Commands & Usage

The `volt` CLI provides comprehensive terminal commands:

| Command | Description | Example |
| :--- | :--- | :--- |
| `volt activate` | Configure server URL, session ID, and personal provider key | `volt activate --user sanjai` |
| `volt code [prompt]` | Generate code or answer technical questions | `volt code "Build a FastAPI rate limiter"` |
| `volt code -f [file]` | Attach file context to the prompt | `volt code -f app/security.py "Find security flaws"` |
| `volt code -i [image]`| Attach UI mockup for visual inspection (Qwen2-VL) | `volt code -i mockup.png "Generate HTML/CSS"` |
| `volt code -w` / `-a` | Auto-extract and write code files to disk | `volt code -w "Create script.py to parse logs"` |
| `volt chat` | Interactive multi-turn terminal chat session | `volt chat` (Supports `/write`, `/apply`, `/models`, `/clear`) |
| `volt models` | View specialist models, licenses, and pipeline tracks | `volt models` |
| `volt test` | Send a ping health check through the proxy | `volt test` |
| `volt usage` | Inspect personal token consumption and request stats | `volt usage` |
| `volt dashboard` | Open the real-time glassmorphism web dashboard | `volt dashboard` |
| `volt env` | Print shell export statements for `OPENAI_BASE_URL` | `volt env --shell powershell` |

---

## 🔄 The BYOK Data Collection Flywheel

VOLT-AI connects model access directly with an automated data collection and fine-tuning flywheel:

```
┌─────────────────────────────────┐
│   Developer / External User     │
│   (Terminal CLI, Cursor, etc.)  │
└────────────────┬────────────────┘
                 │
                 │ 1. Supplies personal provider API key or uses free community tier
                 │    via 'volt activate' or 'Authorization: Bearer <your-key>'
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        ⚡ VOLT-AI Engine                               │
│                                                                        │
│ 2. Rate Limiting & Tier Gatekeeper: Enforces burst quotas.              │
│    (10 req/min for IP, 30 req/min for portal, 120 req/min for BYOK).   │
│                                                                        │
│ 3. Intent Analysis: Routes request to optimal specialists:             │
│    • 'fast_coding': Qwen2.5-Coder                                      │
│    • 'two_pass_reasoning': DeepSeek-R1 (Plan) -> Qwen-Coder (Code)     │
│    • 'vision': Qwen2-VL (Screenshot / UI Analysis)                     │
│                                                                        │
│ 4. Zero-Leak Redaction: Strips API keys, passwords, and tokens.        │
│                                                                        │
│ 5. Data Collection: Records scrubbed prompts, generated code, latency, │
│    and session metrics to PostgreSQL (llm_calls table).                │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Continuous Learning Pipeline                         │
│                                                                        │
│ • POST /admin/export-dataset: Automatically exports SFT and DPO pairs. │
│ • training/train_lora.py: Fine-tunes future open-weight VOLT models   │
│   directly on real-world developer interactions!                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 IDE & Tool Integration

Route your existing developer tools and IDEs through VOLT-AI:

### 1. Cursor / VS Code / Aider / OpenCode (OpenAI SDK Compatible)
Add the following configuration to your terminal profile or IDE settings:

#### Windows PowerShell (`$PROFILE`):
```powershell
$env:OPENAI_BASE_URL = "https://volt-ai-lmgz.onrender.com/v1"
$env:OPENAI_API_KEY  = "your-provider-api-key"   # e.g. OpenRouter, DeepSeek, or Gemini key
$env:X_SESSION_ID    = $env:USERNAME
```

#### Linux / macOS (`~/.bashrc` or `~/.zshrc`):
```bash
export OPENAI_BASE_URL="https://volt-ai-lmgz.onrender.com/v1"
export OPENAI_API_KEY="your-provider-api-key"    # e.g. OpenRouter, DeepSeek, or Gemini key
export X_SESSION_ID="$USER"
```

### 2. Anthropic SDK & Claude CLI
```bash
export ANTHROPIC_BASE_URL="https://volt-ai-lmgz.onrender.com"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 3. Model Name to Use in Tools
Specify either:
- `VOLT-AI` (Primary recommended coordinated model)
- `volt-ai-1.0`

---

## 📊 Live Observability & Cloud Service

- **Central Server**: `https://volt-ai-lmgz.onrender.com`
- **Google Sign-In & Login Portal**: `https://volt-ai-lmgz.onrender.com/login`
- **Interactive Dashboard**: `https://volt-ai-lmgz.onrender.com/dashboard`
- **Health Check**: `https://volt-ai-lmgz.onrender.com/health`
- **API Models Catalog**: `https://volt-ai-lmgz.onrender.com/v1/models`

---

## 🧪 Running Tests

Run the full automated test suite:

```bash
# Run unit & API test suite (179 tests passing, 0 warnings)
pytest -m "not integration"
```

---

## ⚖️ License, Copyright & Credits

### Author & Credits
- **Creator & Lead Architect**: **S Sanjai (Baizo)**
- **GitHub**: [@baizo7](https://github.com/baizo7)
- **Repository**: [https://github.com/baizo7/VOLT](https://github.com/baizo7/VOLT)

### Dual-License Terms
1. **VOLT-AI Model (`volt-ai-1.0`)**: Released under the **Apache License 2.0**. You are free to run inference, fine-tune, and build research applications on top of the model.
2. **VOLT-AI Platform & Backend**: **Proprietary & Source-Available**. Copyright (c) 2026 S Sanjai (Baizo). All rights reserved. The backend proxy architecture, coordination engine, database schemas, and dashboards are protected and cannot be redistributed commercially or hosted as a competing service without authorization.

### Mandatory Attribution
Any application, research paper, derivative model, or service utilizing VOLT-AI must visibly credit:

```text
"Powered by VOLT-AI — Created by Baizo (S Sanjai) | https://github.com/baizo7/VOLT"
```

For licensing inquiries or commercial enterprise deployments, please contact the author via [GitHub](https://github.com/baizo7).
