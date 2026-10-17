# ⚡ VOLT-AI

**Intelligent Multi-Model AI Coordination, Routing & Observability Engine**

[![Author: Baizo](https://img.shields.io/badge/Author-Baizo%20%28S%20Sanjai%29-blue.svg)](https://github.com/baizo7)
[![Model License: Apache 2.0](https://img.shields.io/badge/Model%20License-Apache%202.0%20%28Open%20Source%29-green.svg)](LICENSE)
[![Platform License: Proprietary](https://img.shields.io/badge/Platform%20License-Proprietary%20%2F%20Source--Available-red.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Cloud Endpoint](https://img.shields.io/badge/Render-Live%20Endpoint-46E3B7.svg)](https://volt-ai-lmgz.onrender.com)
[![BYOK Architecture](https://img.shields.io/badge/Access-Bring--Your--Own--Key%20%28BYOK%29-orange.svg)]()

---

> ### ⚠️ Intellectual Property & Licensing Notice
> **The VOLT-AI Model (`volt-ai-1.0` specifications, weights, and inference schema) is released as Open Source under the Apache License 2.0.**
>
> The **VOLT-AI Platform, Core Coordination Engine, Dynamic Multi-Model Router, Secret Scrubbing Pipeline, and Observability Backend** are proprietary intellectual property created by **S Sanjai (Baizo)**. All platform rights are strictly reserved. Commercial redistribution, unauthorized resale, or hosting of competing SaaS proxy services without express prior written permission is prohibited. See [LICENSE](LICENSE) for full legal terms and credits.

---

## 🌟 Overview

VOLT-AI provides next-generation AI coordination, dynamic specialist fallback, real-time observability, and a community model portal:

- **Free Starter Tier (Zero Setup Required)**: Anyone can start coding immediately with `VOLT-AI` without an API key (up to 30 free daily requests).
- **Web Developer Portal & 1-Click API Key Generator**: Visit [volt-ai-lmgz.onrender.com](https://volt-ai-lmgz.onrender.com) to generate your personal `volt_live_...` API key with 50 free requests per day, copy-paste snippets for Python, Cursor, VS Code, and terminal CLI.
- **Bring-Your-Own-Key (BYOK) for Unlimited Power**: Provide your personal provider key (OpenRouter, DeepSeek, Gemini, or OpenAI) for 100% unlimited requests billed to your provider at zero markup.
- **Open-Source VOLT-AI Model (`volt-ai-1.0`)**: Open model card and inference schema for code generation, architectural synthesis, and multi-turn refactoring.
- **Automated Data Collection Flywheel**: All coding activity is scrubbed of credentials and continuously captured into PostgreSQL for fine-tuning future open-source VOLT releases via LoRA and DPO.
- **Client Tooling (`volt-coder` & `volt`)**: Local terminal CLI for one-shot coding, interactive chat sessions, and personal token usage analytics.
- **Universal Drop-in Proxy**: OpenAI & Anthropic API compatible proxy supporting Cursor, Aider, OpenCode, VS Code extensions, and native SDKs.
- **Zero-Leak Secret Redaction**: In-flight redaction of API keys, AWS credentials, GitHub tokens, and private keys before persistence.
- **Live Observability Dashboard**: Real-time glassmorphism analytics dashboard tracking tokens, latency, cost, and test pass rates.

---

## 🔑 3 Ways to Access VOLT-AI

| Tier | API Key Required? | Quota / Limits | Best For |
| :--- | :--- | :--- | :--- |
| **1. Free Starter** | ❌ None | **30 free requests / day** | Instant testing, quick CLI queries, casual terminal scripting |
| **2. Portal Developer Key** | ⚡ `volt_live_...` (1-Click Generate) | **50 free requests / day** | Personal developer projects, VS Code / Cursor plugins, scripts |
| **3. BYOK (Bring Your Own Key)** | 🔑 OpenRouter, DeepSeek, Gemini, OpenAI | ♾️ **Unlimited** | Power users, large codebases, continuous development |

---

## 🔄 The BYOK Data Collection Flywheel

VOLT-AI connects model access directly with an automated data collection and fine-tuning flywheel:

```
┌─────────────────────────────────┐
│   Developer / External User     │
│   (Terminal CLI, Cursor, etc.)  │
└────────────────┬────────────────┘
                 │
                 │ 1. Supplies THEIR OWN provider API key (OpenRouter, DeepSeek, Gemini, OpenAI)
                 │    via 'volt activate' or 'Authorization: Bearer <your-key>'
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        ⚡ VOLT-AI Engine                               │
│                                                                        │
│ 2. BYOK Gatekeeper: Verifies the caller provided an active key.       │
│    (Rejects unauthorized requests with 401).                           │
│                                                                        │
│ 3. Execution: Dispatches request to provider using THE USER'S KEY.     │
│    (The provider bills the user's account — zero cost to host).        │
│                                                                        │
│ 4. Zero-Leak Redaction: Strips API keys, passwords, and tokens.        │
│                                                                        │
│ 5. Data Collection: Records prompts, generated code, latency, and     │
│    session metrics to PostgreSQL (llm_calls table).                    │
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

## 🤖 The VOLT-AI Model (`volt-ai-1.0`)

The **VOLT-AI Model** is released under the **Apache 2.0 Open-Source License**.

### Model Profile
- **Model ID**: `VOLT-AI` / `volt-ai-1.0`
- **Architecture**: Multi-Model Coordinated Specialist Mixture
- **Specializations**: Code synthesis, test-driven repair, system architecture, rapid debugging
- **Access Model**: Bring-Your-Own-Key (BYOK)
- **Context Routing**:
  - `code` track: Specialized code generation and bug fixes
  - `general` track: Multi-turn architectural explanation and reasoning
  - `fast` track: Low-latency autocompletions and edits
  - `creative` track: Novel ideation and documentation

---

## 🛠️ Local Setup Configuration (For Developers & Teams)

You can set up and run the VOLT-AI client locally on your workstation to interact with the VOLT-AI cloud server or your self-hosted instances.

### 1. Clone & Install Client Dependencies

Clone the repository and install the client package locally:

```bash
# Clone the repository
git clone https://github.com/baizo7/VOLT.git
cd VOLT

# Set up a Python virtual environment (Python 3.9+)
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install local client package in editable mode
pip install -e .
```

### 2. Configure Your Client (Free Tier or BYOK)

#### Option A: Zero Configuration (Instant Free Starter Tier)
You do not need an API key to test VOLT-AI! Simply run:
```bash
volt-coder "Write a binary search algorithm in Python"
```
Requests will automatically connect to the free community starter tier (up to 30 requests/day).

#### Option B: Generate a Free Developer Portal Key (50 requests/day)
1. Open the [VOLT-AI Portal](https://volt-ai-lmgz.onrender.com).
2. Switch to the **🔑 Model Portal & API Keys** tab.
3. Click **⚡ Generate My Free VOLT API Key**.
4. Run `volt activate` and paste your `volt_live_...` key.

#### Option C: Bring Your Own Provider Key (Unlimited Usage)
For unlimited requests, run:
```bash
volt activate --server https://volt-ai-lmgz.onrender.com
```
And provide your personal provider API key:
- **OpenRouter** ([openrouter.ai/keys](https://openrouter.ai/keys)) *(Recommended for access to all models)*
- **DeepSeek** ([platform.deepseek.com](https://platform.deepseek.com))
- **Google Gemini** ([aistudio.google.com](https://aistudio.google.com))
- **OpenAI** ([platform.openai.com](https://platform.openai.com))

This saves your local configuration to `~/.volt-ai/config.json`.

---

## 💻 Local CLI Usage (`volt-coder` & `volt`)

Once installed, use the local commands to generate code, chat, and inspect routing:

### One-Shot Code Generation
```bash
# Basic prompt
volt-coder "Write a fast thread-safe LRU cache in Python"

# Include existing files in context
volt-coder code -f app/security.py "Review this file for security vulnerabilities"
```

### Interactive Multi-Turn Terminal Chat
```bash
volt-coder chat
```

### Check Available Specialists & Models
```bash
volt-coder models
```

### Personal Usage Analytics
```bash
# View personal token consumption and latency
volt usage

# Open the real-time web dashboard
volt dashboard
```

---

## 🔌 IDE & Tool Integration

Route your existing developer tools and IDEs through VOLT-AI:

### 1. Cursor / VS Code / Aider / OpenCode (OpenAI SDK Compatible)
Add the following configuration to your terminal profile or IDE settings:

#### Windows PowerShell (`$PROFILE`):
```powershell
$env:OPENAI_BASE_URL = "https://volt-ai-lmgz.onrender.com/v1"
$env:OPENAI_API_KEY  = "your-provider-api-key"   # e.g. OpenRouter, DeepSeek, or OpenAI key
$env:X_SESSION_ID    = $env:USERNAME
```

#### Linux / macOS (`~/.bashrc` or `~/.zshrc`):
```bash
export OPENAI_BASE_URL="https://volt-ai-lmgz.onrender.com/v1"
export OPENAI_API_KEY="your-provider-api-key"    # e.g. OpenRouter, DeepSeek, or OpenAI key
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
- **Interactive Dashboard**: `https://volt-ai-lmgz.onrender.com/dashboard`
- **Health Check**: `https://volt-ai-lmgz.onrender.com/health`
- **API Models Catalog**: `https://volt-ai-lmgz.onrender.com/v1/models`

---

## 🧪 Running Client Tests

Verify your local client installation:

```bash
# Run unit & API test suite (161 tests passing)
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
