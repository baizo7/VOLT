"""
VOLT-AI — Documentation & Installation Web Portal
Glassmorphic cyber documentation interface covering 1-click PyPI installation,
CLI commands, IDE configurations, API reference, and multi-model architecture.
"""

DOCS_HTML = r"""<!DOCTYPE html>
<html lang="en" class="h-full bg-[#0a0e1a] text-slate-100 scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Documentation & Installation Guide — VOLT-AI</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700;800;900&display=swap">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] },
          colors: {
            surface: { 950: '#0a0e1a', 900: '#0f1424', 850: '#13192c', 800: '#161d30', 700: '#1e2740', 600: '#283350' },
          }
        }
      }
    }
  </script>
  <style>
    body { font-family: 'Inter', sans-serif; background-color: #0a0e1a; }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .glass { background: rgba(15, 20, 36, 0.75); backdrop-filter: blur(16px); }
    .glass-card { background: rgba(15, 20, 36, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(79, 70, 229, 0.25); }
    .glass-code { background: rgba(10, 14, 26, 0.95); border: 1px solid rgba(79, 70, 229, 0.2); }
    .glow-indigo { box-shadow: 0 0 50px rgba(79, 70, 229, 0.15); }
    .glow-amber { box-shadow: 0 0 40px rgba(245, 158, 11, 0.15); }
    .nav-link.active { color: #818cf8; border-color: #818cf8; }
    pre { scrollbar-width: thin; scrollbar-color: #374151 transparent; }
    pre::-webkit-scrollbar { height: 6px; }
    pre::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
  </style>
</head>
<body class="min-h-full flex flex-col justify-between relative selection:bg-indigo-600 selection:text-white">

  <!-- Ambient Glow Backgrounds -->
  <div class="fixed top-[-100px] left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-tr from-indigo-600/15 via-violet-600/10 to-transparent rounded-full blur-[140px] pointer-events-none"></div>
  <div class="fixed bottom-[-150px] right-[-100px] w-[600px] h-[400px] bg-gradient-to-tl from-amber-500/10 via-indigo-600/5 to-transparent rounded-full blur-[120px] pointer-events-none"></div>

  <!-- Top Sticky Navigation -->
  <header class="sticky top-0 z-50 glass border-b border-surface-700/60 px-4 md:px-8 py-3.5">
    <div class="max-w-7xl mx-auto flex items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <a href="/docs" class="flex items-center gap-2.5 group">
          <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-amber-500 via-indigo-600 to-violet-600 flex items-center justify-center font-black text-white text-base shadow-lg shadow-amber-500/20 group-hover:scale-105 transition-transform">⚡</div>
          <div class="flex items-baseline gap-1.5">
            <span class="text-xl font-black tracking-tight text-white"><span class="text-amber-400">VOLT</span><span class="text-indigo-400">-AI</span></span>
            <span class="text-[11px] font-bold text-slate-400 px-2 py-0.5 rounded-full bg-surface-800 border border-surface-700">Docs & Install</span>
          </div>
        </a>
      </div>

      <nav class="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-300">
        <a href="#quickstart" class="hover:text-amber-400 transition">Quickstart</a>
        <a href="#installation" class="hover:text-indigo-400 transition">Installation</a>
        <a href="#cli-commands" class="hover:text-indigo-400 transition">CLI Commands</a>
        <a href="#ide-setup" class="hover:text-indigo-400 transition">IDE & Tools</a>
        <a href="#specialists" class="hover:text-indigo-400 transition">Specialists</a>
        <a href="#api-reference" class="hover:text-indigo-400 transition">REST API</a>
      </nav>

      <div class="flex items-center gap-2.5">
        <a href="/dashboard" class="px-3 py-1.5 text-xs font-bold rounded-lg bg-surface-800 hover:bg-surface-700 border border-surface-700 text-slate-200 transition flex items-center gap-1.5 shadow-sm">
          <span>📊</span>
          <span class="hidden sm:inline">Dashboard</span>
        </a>
        <a href="/login" class="px-3 py-1.5 text-xs font-bold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-1.5 shadow-md shadow-indigo-600/30">
          <span>🔑</span>
          <span>Sign In / Get Key</span>
        </a>
        <a href="https://github.com/baizo7/VOLT" target="_blank" class="p-1.5 text-slate-400 hover:text-white transition rounded-lg hover:bg-surface-800" title="GitHub Repository">
          <svg class="h-5 w-5 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        </a>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="max-w-7xl mx-auto px-4 md:px-8 pt-12 pb-8 w-full text-center lg:text-left relative z-10">
    <div class="flex flex-col lg:flex-row items-center justify-between gap-10">
      <div class="max-w-2xl space-y-5">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
          <span class="h-2 w-2 rounded-full bg-amber-400 animate-pulse"></span>
          <span>VOLT-AI v1.0.0 Global Release &bull; Publicly Available</span>
        </div>
        
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white leading-[1.1]">
          Code Smarter with <span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-indigo-400 to-violet-400">VOLT-AI</span>
        </h1>
        
        <p class="text-slate-300 text-base md:text-lg leading-relaxed">
          The autonomous multi-model AI coordination, routing, and observability engine. 
          Combines DeepSeek-R1, Qwen2.5-Coder, and multimodal specialists under a single drop-in OpenAI/Anthropic API with zero-leak privacy.
        </p>

        <!-- 1-Click Install Command Pill -->
        <div class="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div class="flex items-center justify-between gap-3 px-4 py-3 rounded-xl glass-code text-left flex-1 font-mono text-sm text-indigo-300 shadow-xl border border-indigo-500/30">
            <div class="flex items-center gap-2.5">
              <span class="text-amber-400 select-none">$</span>
              <span id="hero-install-cmd">pip install volt-ai</span>
            </div>
            <button onclick="copyToClipboard('pip install volt-ai', this)" class="px-2.5 py-1 text-xs bg-indigo-600/40 hover:bg-indigo-600 text-indigo-200 rounded-md transition flex items-center gap-1 font-sans font-semibold">
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
              <span>Copy</span>
            </button>
          </div>

          <a href="#quickstart" class="px-5 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/25 transition text-center shrink-0">
            Get Started &rarr;
          </a>
        </div>

        <!-- Badges Row -->
        <div class="flex flex-wrap items-center justify-center lg:justify-start gap-2 pt-2 text-xs font-mono">
          <span class="px-2.5 py-1 rounded-md bg-surface-900 border border-surface-700 text-slate-300">PyPI: v1.0.0</span>
          <span class="px-2.5 py-1 rounded-md bg-surface-900 border border-surface-700 text-slate-300">Python: 3.9+</span>
          <span class="px-2.5 py-1 rounded-md bg-emerald-950/60 border border-emerald-800/60 text-emerald-300">179 Tests: Passed (100%)</span>
          <span class="px-2.5 py-1 rounded-md bg-indigo-950/60 border border-indigo-800/60 text-indigo-300">License: Apache-2.0</span>
        </div>
      </div>

      <!-- Quick Feature Matrix Cards -->
      <div class="w-full max-w-md grid grid-cols-2 gap-3.5 text-left">
        <div class="p-4 rounded-2xl bg-surface-900/80 border border-surface-700/60 space-y-2">
          <div class="text-2xl">⚡</div>
          <h3 class="text-sm font-bold text-white">Free Community Tier</h3>
          <p class="text-xs text-slate-400">30 free daily requests without needing any API key.</p>
        </div>
        <div class="p-4 rounded-2xl bg-surface-900/80 border border-surface-700/60 space-y-2">
          <div class="text-2xl">🔑</div>
          <h3 class="text-sm font-bold text-white">BYOK Unlimited</h3>
          <p class="text-xs text-slate-400">Attach OpenRouter, DeepSeek, or Gemini keys at 0 markup.</p>
        </div>
        <div class="p-4 rounded-2xl bg-surface-900/80 border border-surface-700/60 space-y-2">
          <div class="text-2xl">🧠</div>
          <h3 class="text-sm font-bold text-white">2-Pass Reasoning</h3>
          <p class="text-xs text-slate-400">DeepSeek-R1 plans the architecture &rarr; Qwen writes the code.</p>
        </div>
        <div class="p-4 rounded-2xl bg-surface-900/80 border border-surface-700/60 space-y-2">
          <div class="text-2xl">🛡️</div>
          <h3 class="text-sm font-bold text-white">Zero-Leak Redaction</h3>
          <p class="text-xs text-slate-400">In-flight regex scrubs all passwords, tokens, and secrets.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Main Content Layout with Sidebar -->
  <div class="max-w-7xl mx-auto px-4 md:px-8 py-10 w-full flex-1 flex flex-col lg:flex-row gap-10 relative z-10">
    
    <!-- Sidebar / Table of Contents -->
    <aside class="hidden lg:block w-64 shrink-0 space-y-6 sticky top-24 self-start">
      <div class="glass-card rounded-2xl p-5 space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">On This Page</h4>
        <nav class="space-y-1.5 text-xs font-medium">
          <a href="#quickstart" class="block py-1 text-slate-300 hover:text-white transition">1. 30-Second Quickstart</a>
          <a href="#installation" class="block py-1 text-slate-300 hover:text-white transition">2. Installation Options</a>
          <a href="#cli-commands" class="block py-1 text-slate-300 hover:text-white transition">3. CLI Commands Cheat Sheet</a>
          <a href="#ide-setup" class="block py-1 text-slate-300 hover:text-white transition">4. IDE Integration (Cursor/VSCode)</a>
          <a href="#specialists" class="block py-1 text-slate-300 hover:text-white transition">5. Specialist Roster & Routing</a>
          <a href="#access-tiers" class="block py-1 text-slate-300 hover:text-white transition">6. Access Tiers & Rate Limits</a>
          <a href="#api-reference" class="block py-1 text-slate-300 hover:text-white transition">7. REST API Reference</a>
          <a href="#security" class="block py-1 text-slate-300 hover:text-white transition">8. Security & Data Privacy</a>
        </nav>
      </div>

      <div class="glass rounded-2xl p-5 border border-surface-700/60 space-y-3">
        <h5 class="text-xs font-bold text-white flex items-center gap-1.5">
          <span>🚀</span> Public Server Status
        </h5>
        <div class="space-y-2 text-[11px] text-slate-400">
          <div class="flex items-center justify-between">
            <span>Status</span>
            <span class="text-emerald-400 font-bold flex items-center gap-1">
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span> ONLINE
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span>Endpoint</span>
            <span class="font-mono text-slate-300 text-[10px]">volt-ai-lmgz.onrender.com</span>
          </div>
          <div class="flex items-center justify-between">
            <span>Rate Limiting</span>
            <span class="text-indigo-400 font-semibold">Active (SlowAPI)</span>
          </div>
        </div>
        <a href="/dashboard" class="block w-full py-2 text-center text-xs font-bold rounded-xl bg-surface-800 hover:bg-surface-700 border border-surface-600 text-white transition">
          View Live Telemetry
        </a>
      </div>
    </aside>

    <!-- Main Content Articles -->
    <main class="flex-1 space-y-16 max-w-4xl">

      <!-- SECTION 1: 30-Second Quickstart -->
      <section id="quickstart" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-amber-400 text-xs font-mono font-bold uppercase tracking-wider">Step 1</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">30-Second Quickstart</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          VOLT-AI requires zero complex setup. Install the CLI directly from PyPI, run the automated health ping, and begin generating code immediately:
        </p>

        <div class="space-y-3 pt-2">
          <!-- Step 1 -->
          <div class="glass-card rounded-2xl p-5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-400 font-mono">1. Install CLI from PyPI</span>
              <button onclick="copyToClipboard('pip install volt-ai', this)" class="text-xs text-slate-400 hover:text-white transition">Copy</button>
            </div>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code>pip install volt-ai</code></pre>
          </div>

          <!-- Step 2 -->
          <div class="glass-card rounded-2xl p-5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-400 font-mono">2. Verify Connectivity</span>
              <button onclick="copyToClipboard('volt test', this)" class="text-xs text-slate-400 hover:text-white transition">Copy</button>
            </div>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code>volt test</code></pre>
            <p class="text-[11px] text-slate-400">Verifies connection to the public server and confirms specialist candidate readiness.</p>
          </div>

          <!-- Step 3 -->
          <div class="glass-card rounded-2xl p-5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-400 font-mono">3. Generate Code and Write to Disk</span>
              <button onclick="copyToClipboard('volt code -w &quot;Create a python script to parse CSV files and compute averages&quot;', this)" class="text-xs text-slate-400 hover:text-white transition">Copy</button>
            </div>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code>volt code -w "Create a python script to parse CSV files and compute averages"</code></pre>
            <p class="text-[11px] text-slate-400">The <code>-w</code> flag automatically parses fenced code blocks and saves clean files with designated filenames.</p>
          </div>
        </div>
      </section>

      <!-- SECTION 2: Installation Options -->
      <section id="installation" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-indigo-400 text-xs font-mono font-bold uppercase tracking-wider">Step 2</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">Installation Options</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          Choose the installation method suited to your environment:
        </p>

        <!-- Tabbed Container -->
        <div class="glass-card rounded-2xl overflow-hidden border border-surface-700/80">
          <!-- Tab Headers -->
          <div class="flex border-b border-surface-700 bg-surface-900/60 p-2 gap-2 text-xs font-semibold overflow-x-auto">
            <button onclick="switchTab('install', 'pypi', this)" class="install-tab px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold transition">PyPI Package (Recommended)</button>
            <button onclick="switchTab('install', 'source', this)" class="install-tab px-4 py-2 rounded-xl text-slate-400 hover:text-white transition">From Source (Editable)</button>
            <button onclick="switchTab('install', 'docker', this)" class="install-tab px-4 py-2 rounded-xl text-slate-400 hover:text-white transition">Self-Hosted Server (Docker)</button>
          </div>

          <!-- Tab Content: PyPI -->
          <div id="tab-install-pypi" class="p-6 space-y-4">
            <h4 class="text-sm font-bold text-white">Universal Python Package</h4>
            <p class="text-xs text-slate-300 leading-relaxed">
              Installs the lightweight zero-dependency CLI package. Works on Windows, macOS, and Linux with Python 3.9+.
            </p>
            <div class="space-y-2">
              <span class="text-[11px] font-mono text-slate-400">Command:</span>
              <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300"><code>pip install volt-ai</code></pre>
            </div>
            <div class="space-y-2">
              <span class="text-[11px] font-mono text-slate-400">To upgrade to the latest version at any time:</span>
              <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300"><code>pip install --upgrade volt-ai</code></pre>
            </div>
          </div>

          <!-- Tab Content: Source -->
          <div id="tab-install-source" class="p-6 space-y-4 hidden">
            <h4 class="text-sm font-bold text-white">Clone and Install in Editable Mode</h4>
            <p class="text-xs text-slate-300 leading-relaxed">
              Recommended for contributors modifying routing logic, benchmarks, or training scripts:
            </p>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code># 1. Clone the repository
git clone https://github.com/baizo7/VOLT.git
cd VOLT

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 4. Install in editable mode with development dependencies
pip install -e .
pip install -r requirements.txt</code></pre>
          </div>

          <!-- Tab Content: Docker -->
          <div id="tab-install-docker" class="p-6 space-y-4 hidden">
            <h4 class="text-sm font-bold text-white">Self-Host Your Own Server</h4>
            <p class="text-xs text-slate-300 leading-relaxed">
              Run VOLT-AI on your own private infrastructure with PostgreSQL 16 and pgvector:
            </p>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code># 1. Spin up PostgreSQL with pgvector extension
docker compose up -d db

# 2. Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4</code></pre>
          </div>
        </div>
      </section>

      <!-- SECTION 3: CLI Commands Cheat Sheet -->
      <section id="cli-commands" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-amber-400 text-xs font-mono font-bold uppercase tracking-wider">Step 3</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">CLI Commands Cheat Sheet</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          The <code>volt</code> and <code>volt-coder</code> executables offer rich terminal subcommands:
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <!-- Command: activate -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt activate</span>
              <span class="text-[10px] text-slate-400">Terminal Setup</span>
            </div>
            <p class="text-xs text-slate-300">Configures server URL, developer session username, and attaches your personal provider key for unlimited requests.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt activate --user sanjai</code></pre>
          </div>

          <!-- Command: code -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt code "..."</span>
              <span class="text-[10px] text-slate-400">Code Synthesis</span>
            </div>
            <p class="text-xs text-slate-300">Executes single-pass code generation or technical answers. Add <code>-w</code> to auto-write files to disk.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt code -w "Build a FastAPI rate limiter"</code></pre>
          </div>

          <!-- Command: code with file context -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt code -f ...</span>
              <span class="text-[10px] text-slate-400">File Context</span>
            </div>
            <p class="text-xs text-slate-300">Passes local file contents into the prompt for debugging, refactoring, or security reviews.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt code -f app/security.py "Audit secrets"</code></pre>
          </div>

          <!-- Command: code with image context -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt code -i ...</span>
              <span class="text-[10px] text-slate-400">UI Vision (Qwen2-VL)</span>
            </div>
            <p class="text-xs text-slate-300">Inspects UI mockups or screenshot images and writes matching frontend code.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt code -i mockup.png -w "Generate HTML"</code></pre>
          </div>

          <!-- Command: chat -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt chat</span>
              <span class="text-[10px] text-slate-400">Interactive REPL</span>
            </div>
            <p class="text-xs text-slate-300">Launches a multi-turn terminal chat with internal commands: <code>/write [file]</code>, <code>/apply</code>, <code>/models</code>, <code>/clear</code>.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt chat</code></pre>
          </div>

          <!-- Command: models -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt models</span>
              <span class="text-[10px] text-slate-400">Model Roster</span>
            </div>
            <p class="text-xs text-slate-300">Displays active open-weight specialists, licenses, cloud fallbacks, and activation tracks.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt models</code></pre>
          </div>

          <!-- Command: usage -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt usage</span>
              <span class="text-[10px] text-slate-400">Personal Telemetry</span>
            </div>
            <p class="text-xs text-slate-300">Inspects your daily token usage, request latency, and quota consumption.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt usage</code></pre>
          </div>

          <!-- Command: dashboard -->
          <div class="glass-card rounded-2xl p-5 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">volt dashboard</span>
              <span class="text-[10px] text-slate-400">Web Analytics</span>
            </div>
            <p class="text-xs text-slate-300">Opens the visual real-time analytics web dashboard in your default browser.</p>
            <pre class="glass-code rounded-lg p-2.5 font-mono text-[11px] text-slate-300"><code>volt dashboard</code></pre>
          </div>
        </div>
      </section>

      <!-- SECTION 4: IDE & Tool Integration -->
      <section id="ide-setup" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-indigo-400 text-xs font-mono font-bold uppercase tracking-wider">Step 4</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">IDE & Tool Integration</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          Because VOLT-AI implements standard OpenAI and Anthropic proxy specifications, it works out-of-the-box with any modern AI coding tool:
        </p>

        <!-- IDE Tabs -->
        <div class="glass-card rounded-2xl overflow-hidden border border-surface-700/80">
          <div class="flex border-b border-surface-700 bg-surface-900/60 p-2 gap-2 text-xs font-semibold overflow-x-auto">
            <button onclick="switchTab('ide', 'cursor', this)" class="ide-tab px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold transition">Cursor IDE</button>
            <button onclick="switchTab('ide', 'vscode', this)" class="ide-tab px-4 py-2 rounded-xl text-slate-400 hover:text-white transition">VS Code Continue / Cline</button>
            <button onclick="switchTab('ide', 'python', this)" class="ide-tab px-4 py-2 rounded-xl text-slate-400 hover:text-white transition">Python OpenAI SDK</button>
            <button onclick="switchTab('ide', 'claude', this)" class="ide-tab px-4 py-2 rounded-xl text-slate-400 hover:text-white transition">Claude CLI</button>
          </div>

          <!-- Tab Content: Cursor -->
          <div id="tab-ide-cursor" class="p-6 space-y-4">
            <h4 class="text-sm font-bold text-white">Configuring Cursor</h4>
            <ol class="list-decimal list-inside text-xs text-slate-300 space-y-2 leading-relaxed">
              <li>Open Cursor &rarr; <strong>Settings</strong> &rarr; <strong>Cursor Settings</strong> &rarr; <strong>Models</strong>.</li>
              <li>Under <strong>OpenAI API Key</strong>, toggle <strong>Override OpenAI Base URL</strong> to <code>ON</code>.</li>
              <li>Set Base URL to: <code class="text-indigo-300 font-mono">https://volt-ai-lmgz.onrender.com/v1</code></li>
              <li>Enter your personal provider API key or portal key starting with <code class="text-indigo-300 font-mono">volt_live_...</code>.</li>
              <li>Add model name: <code class="text-amber-400 font-mono font-bold">VOLT-AI</code>.</li>
            </ol>
          </div>

          <!-- Tab Content: VS Code -->
          <div id="tab-ide-vscode" class="p-6 space-y-4 hidden">
            <h4 class="text-sm font-bold text-white">Continue Extension (<code class="text-indigo-300">~/.continue/config.json</code>)</h4>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code>{
  "models": [
    {
      "title": "VOLT-AI Autonomous Mixture",
      "provider": "openai",
      "model": "VOLT-AI",
      "apiBase": "https://volt-ai-lmgz.onrender.com/v1",
      "apiKey": "your-key-here"
    }
  ]
}</code></pre>
          </div>

          <!-- Tab Content: Python SDK -->
          <div id="tab-ide-python" class="p-6 space-y-4 hidden">
            <h4 class="text-sm font-bold text-white">Standard OpenAI Python Library</h4>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code>from openai import OpenAI

client = OpenAI(
    base_url="https://volt-ai-lmgz.onrender.com/v1",
    api_key="your-api-key"  # Or free community tier: "volt-cloud"
)

response = client.chat.completions.create(
    model="VOLT-AI",
    messages=[
        {"role": "user", "content": "Write a binary search function in Python"}
    ]
)

print(response.choices[0].message.content)</code></pre>
          </div>

          <!-- Tab Content: Claude CLI -->
          <div id="tab-ide-claude" class="p-6 space-y-4 hidden">
            <h4 class="text-sm font-bold text-white">Anthropic SDK & Claude CLI Environment</h4>
            <pre class="glass-code rounded-xl p-3.5 font-mono text-xs text-indigo-300 overflow-x-auto"><code># Windows PowerShell:
$env:ANTHROPIC_BASE_URL="https://volt-ai-lmgz.onrender.com"
$env:ANTHROPIC_API_KEY="your-anthropic-key"

# Linux / macOS:
export ANTHROPIC_BASE_URL="https://volt-ai-lmgz.onrender.com"
export ANTHROPIC_API_KEY="your-anthropic-key"</code></pre>
          </div>
        </div>
      </section>

      <!-- SECTION 5: Specialists & Routing -->
      <section id="specialists" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-amber-400 text-xs font-mono font-bold uppercase tracking-wider">Step 5</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">Specialist Roster & Two-Pass Pipeline</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          VOLT-AI orchestrates 5 dedicated open-weight specialists under a permissive Apache 2.0 / MIT licensing model:
        </p>

        <div class="space-y-3 pt-2">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
              <thead>
                <tr class="border-b border-surface-700 text-slate-400 font-mono">
                  <th class="py-2.5 px-3">Specialist</th>
                  <th class="py-2.5 px-3">Primary Model</th>
                  <th class="py-2.5 px-3">Role & Capability</th>
                  <th class="py-2.5 px-3">License</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-800 text-slate-300 font-mono">
                <tr>
                  <td class="py-3 px-3 text-amber-400 font-bold">fast_coder</td>
                  <td class="py-3 px-3">Qwen2.5-Coder-1.5B / 32B</td>
                  <td class="py-3 px-3 font-sans">Rapid syntax generation and quick bug repair</td>
                  <td class="py-3 px-3 text-emerald-400">Apache 2.0</td>
                </tr>
                <tr>
                  <td class="py-3 px-3 text-indigo-400 font-bold">deep_reasoner</td>
                  <td class="py-3 px-3">DeepSeek-R1 (7B / 671B)</td>
                  <td class="py-3 px-3 font-sans">Chain-of-thought, architectural blueprints, edge cases</td>
                  <td class="py-3 px-3 text-emerald-400">MIT</td>
                </tr>
                <tr>
                  <td class="py-3 px-3 text-cyan-400 font-bold">heavy_coder</td>
                  <td class="py-3 px-3">Qwen2.5-Coder-32B</td>
                  <td class="py-3 px-3 font-sans">Multi-file refactoring, large system components</td>
                  <td class="py-3 px-3 text-emerald-400">Apache 2.0</td>
                </tr>
                <tr>
                  <td class="py-3 px-3 text-violet-400 font-bold">math_specialist</td>
                  <td class="py-3 px-3">Qwen2.5-Math-7B</td>
                  <td class="py-3 px-3 font-sans">Numerical proofs, matrix mathematics & algorithms</td>
                  <td class="py-3 px-3 text-emerald-400">Apache 2.0</td>
                </tr>
                <tr>
                  <td class="py-3 px-3 text-rose-400 font-bold">vision_specialist</td>
                  <td class="py-3 px-3">Qwen2-VL-7B</td>
                  <td class="py-3 px-3 font-sans">UI mockups, screenshot analysis, HTML generation</td>
                  <td class="py-3 px-3 text-emerald-400">Apache 2.0</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- SECTION 6: Access Tiers & Rate Limits -->
      <section id="access-tiers" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-indigo-400 text-xs font-mono font-bold uppercase tracking-wider">Step 6</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">Access Tiers & Burst Rate Limits</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          To protect community infrastructure from automated bot abuse while ensuring unlimited power for developers, VOLT-AI enforces tiered rate limits:
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <!-- Tier 1 -->
          <div class="glass-card rounded-2xl p-5 space-y-3 border-amber-500/30">
            <span class="text-xs font-mono font-bold text-amber-400">COMMUNITY TIER</span>
            <h4 class="text-lg font-black text-white">Free Starter</h4>
            <div class="space-y-1 text-xs text-slate-300">
              <p>&bull; <strong>30 requests / day</strong></p>
              <p>&bull; <strong>10 requests / min</strong> burst limit</p>
              <p>&bull; No credit card or API key required</p>
            </div>
            <p class="text-[11px] text-slate-400 pt-2 border-t border-surface-700">Perfect for trying out VOLT CLI in your terminal.</p>
          </div>

          <!-- Tier 2 -->
          <div class="glass-card rounded-2xl p-5 space-y-3 border-indigo-500/30">
            <span class="text-xs font-mono font-bold text-indigo-400">PORTAL KEY</span>
            <h4 class="text-lg font-black text-white">Developer Tier</h4>
            <div class="space-y-1 text-xs text-slate-300">
              <p>&bull; <strong>50 requests / day</strong></p>
              <p>&bull; <strong>30 requests / min</strong> burst limit</p>
              <p>&bull; 1-click generation via Google Login</p>
            </div>
            <a href="/login" class="inline-block mt-2 text-xs font-bold text-indigo-400 hover:text-indigo-300">Generate Key at /login &rarr;</a>
          </div>

          <!-- Tier 3 -->
          <div class="glass-card rounded-2xl p-5 space-y-3 border-emerald-500/30">
            <span class="text-xs font-mono font-bold text-emerald-400">BYOK POWER</span>
            <h4 class="text-lg font-black text-white">Unlimited Tier</h4>
            <div class="space-y-1 text-xs text-slate-300">
              <p>&bull; <strong>Unlimited daily requests</strong></p>
              <p>&bull; <strong>120 requests / min</strong> burst limit</p>
              <p>&bull; Supply OpenRouter, DeepSeek, or Gemini key</p>
            </div>
            <p class="text-[11px] text-slate-400 pt-2 border-t border-surface-700">Direct provider billing with 0% proxy markup.</p>
          </div>
        </div>
      </section>

      <!-- SECTION 7: REST API Reference -->
      <section id="api-reference" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-amber-400 text-xs font-mono font-bold uppercase tracking-wider">Step 7</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">REST API Reference</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          Direct HTTP endpoint specification for custom integrations and programmatic access:
        </p>

        <div class="space-y-4 pt-2">
          <!-- Chat completions -->
          <div class="glass-card rounded-2xl p-5 space-y-3">
            <div class="flex items-center gap-2 font-mono text-xs">
              <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">POST</span>
              <span class="text-white font-bold">/v1/chat/completions</span>
            </div>
            <p class="text-xs text-slate-300">OpenAI compatible chat completions endpoint. Supports SSE streaming (<code>"stream": true</code>).</p>
            <div class="space-y-1.5">
              <span class="text-[11px] text-slate-400 font-mono">cURL Example:</span>
              <pre class="glass-code rounded-xl p-3 font-mono text-xs text-indigo-300 overflow-x-auto"><code>curl -X POST https://volt-ai-lmgz.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "VOLT-AI",
    "messages": [{"role": "user", "content": "Write quicksort in python"}],
    "stream": false
  }'</code></pre>
            </div>
          </div>

          <!-- Anthropic messages -->
          <div class="glass-card rounded-2xl p-5 space-y-3">
            <div class="flex items-center gap-2 font-mono text-xs">
              <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">POST</span>
              <span class="text-white font-bold">/v1/messages</span>
            </div>
            <p class="text-xs text-slate-300">Anthropic Messages API compatibility endpoint for Claude CLI and tooling.</p>
          </div>

          <!-- Health -->
          <div class="glass-card rounded-2xl p-5 space-y-3">
            <div class="flex items-center gap-2 font-mono text-xs">
              <span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">GET</span>
              <span class="text-white font-bold">/health</span>
            </div>
            <p class="text-xs text-slate-300">Database-aware readiness check. Returns <code>{"ok": true, "status": "ready"}</code>.</p>
          </div>
        </div>
      </section>

      <!-- SECTION 8: Security & Privacy -->
      <section id="security" class="space-y-4">
        <div class="border-b border-surface-700/80 pb-3">
          <span class="text-indigo-400 text-xs font-mono font-bold uppercase tracking-wider">Step 8</span>
          <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight mt-1">Zero-Leak Security & Data Privacy</h2>
        </div>
        <p class="text-sm text-slate-300 leading-relaxed">
          VOLT-AI was engineered from the ground up for strict privacy protection in enterprise and developer environments:
        </p>

        <div class="glass-card rounded-2xl p-6 space-y-4 text-xs text-slate-300 leading-relaxed">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <h5 class="text-white font-bold flex items-center gap-1.5">
                <span>🛡️</span> In-Flight Regex Redaction
              </h5>
              <p class="text-slate-400">All prompt strings, responses, and execution errors pass through an automated secret filter before reaching storage. Secrets are replaced with <code>[REDACTED]</code>.</p>
            </div>
            <div class="space-y-1.5">
              <h5 class="text-white font-bold flex items-center gap-1.5">
                <span>🔒</span> Redacted Credential Formats
              </h5>
              <p class="text-slate-400">Automatically detects OpenAI (<code>sk-...</code>), Anthropic (<code>sk-ant-...</code>), OpenRouter (<code>sk-or-...</code>), Google AIza tokens, AWS Access Keys, GitHub PATs, and DB URIs.</p>
            </div>
          </div>
        </div>
      </section>

    </main>
  </div>

  <!-- Footer -->
  <footer class="w-full glass border-t border-surface-700/60 px-6 py-8 mt-16 relative z-20">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400">
      <div class="flex items-center gap-2">
        <span class="font-bold text-white">⚡ VOLT-AI</span>
        <span>&bull; Created by <a href="https://github.com/baizo7" target="_blank" class="text-amber-400 hover:underline font-semibold">Baizo (S Sanjai)</a></span>
      </div>
      <div class="flex items-center gap-6">
        <a href="/docs" class="hover:text-white transition">Documentation</a>
        <a href="/dashboard" class="hover:text-white transition">Live Dashboard</a>
        <a href="/login" class="hover:text-white transition">Developer Login</a>
        <a href="https://github.com/baizo7/VOLT" target="_blank" class="hover:text-white transition">GitHub Repository</a>
      </div>
    </div>
  </footer>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-6 right-6 z-50 transform translate-y-10 opacity-0 transition-all duration-200 pointer-events-none px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-sans text-xs font-bold shadow-2xl flex items-center gap-2 border border-indigo-400/40">
    <span>✓</span>
    <span id="toast-msg">Copied to clipboard!</span>
  </div>

  <!-- JavaScript for Tabs, Copying, and Active Scrolling -->
  <script>
    function copyToClipboard(text, btn) {
      navigator.clipboard.writeText(text).then(() => {
        showToast("Copied to clipboard!");
        if (btn) {
          const original = btn.innerHTML;
          btn.innerHTML = '<span class="text-emerald-300 font-bold">✓ Copied!</span>';
          setTimeout(() => { btn.innerHTML = original; }, 1800);
        }
      }).catch(err => {
        console.error("Copy failed", err);
      });
    }

    function showToast(msg) {
      const toast = document.getElementById("toast");
      const toastMsg = document.getElementById("toast-msg");
      toastMsg.textContent = msg;
      toast.classList.remove("translate-y-10", "opacity-0");
      setTimeout(() => {
        toast.classList.add("translate-y-10", "opacity-0");
      }, 2000);
    }

    function switchTab(group, target, clickedBtn) {
      // Deactivate all buttons in group
      const buttons = document.querySelectorAll(`.${group}-tab`);
      buttons.forEach(b => {
        b.classList.remove("bg-indigo-600", "text-white", "font-bold");
        b.classList.add("text-slate-400");
      });
      // Activate clicked button
      clickedBtn.classList.add("bg-indigo-600", "text-white", "font-bold");
      clickedBtn.classList.remove("text-slate-400");

      // Hide all content containers in group
      const containers = document.querySelectorAll(`[id^="tab-${group}-"]`);
      containers.forEach(c => c.classList.add("hidden"));

      // Show selected container
      const activeContainer = document.getElementById(`tab-${group}-${target}`);
      if (activeContainer) {
        activeContainer.classList.remove("hidden");
      }
    }
  </script>
</body>
</html>
"""
