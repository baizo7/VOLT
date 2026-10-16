"""
AI Model Observer — Full-Featured Analytics Dashboard
Role-based access control with Admin and Developer views.
Features: Trace Inspector, Dataset Export, Time-Series Charts,
IDE Setup Assistant, Cost Analytics, Model Comparison.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="h-full bg-[#0a0e1a] text-slate-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Model Observer</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700;800&display=swap">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] },
          colors: {
            surface: { 950: '#0a0e1a', 900: '#0f1424', 800: '#161d30', 700: '#1e2740', 600: '#283350' },
          }
        }
      }
    }
  </script>
  <style>
    body { font-family: 'Inter', sans-serif; }
    code, pre, .mono { font-family: 'JetBrains Mono', monospace; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #283350; border-radius: 3px; }
    .glass { background: rgba(15,20,36,0.7); backdrop-filter: blur(12px); }
    .tab-active { background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; box-shadow: 0 4px 15px rgba(79,70,229,0.3); }
    .tab-inactive { background: transparent; color: #94a3b8; }
    .tab-inactive:hover { color: #e2e8f0; background: rgba(30,39,64,0.5); }
    .card { background: #0f1424; border: 1px solid #1e2740; border-radius: 16px; }
    .card-glow { box-shadow: 0 0 30px rgba(79,70,229,0.05); }
    .slide-enter { animation: slideIn 0.25s ease-out; }
    @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    .fade-in { animation: fadeIn 0.2s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .metric-gradient-1 { background: linear-gradient(135deg, rgba(79,70,229,0.12), rgba(124,58,237,0.06)); border-color: rgba(79,70,229,0.25); }
    .metric-gradient-2 { background: linear-gradient(135deg, rgba(6,182,212,0.12), rgba(34,211,238,0.06)); border-color: rgba(6,182,212,0.25); }
    .metric-gradient-3 { background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(52,211,153,0.06)); border-color: rgba(16,185,129,0.25); }
    .metric-gradient-4 { background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(251,191,36,0.06)); border-color: rgba(245,158,11,0.25); }
    .copy-btn:active { transform: scale(0.95); }
  </style>
</head>
<body class="min-h-full flex flex-col">

<!-- ========== HEADER ========== -->
<header class="sticky top-0 z-40 glass border-b border-surface-700 px-4 md:px-6 py-3">
  <div class="max-w-[1440px] mx-auto flex flex-wrap items-center justify-between gap-3">
    <div class="flex items-center gap-3">
      <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center font-extrabold text-white text-sm shadow-lg shadow-indigo-500/20">O</div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-lg font-bold tracking-tight text-white">AI Observer</h1>
          <span id="role-badge" class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-surface-800 text-slate-400 border border-surface-700">...</span>
        </div>
        <p class="text-[11px] text-slate-500 -mt-0.5">Capture Proxy &bull; Telemetry &bull; Fine-Tuning Pipeline</p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <span id="health-badge" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
        <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>Connecting
      </span>
      <span id="live-badge" title="WebSocket Live Telemetry Stream" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-indigo-950/60 text-indigo-400 border border-indigo-800/50">
        <span id="live-dot" class="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse"></span><span id="live-text">Live WS</span>
      </span>
      <button onclick="fetchData()" class="px-2.5 py-1.5 text-[11px] font-medium bg-surface-800 hover:bg-surface-700 text-slate-300 rounded-lg border border-surface-700 transition">Refresh</button>
      <button onclick="openAccessModal()" class="px-2.5 py-1.5 text-[11px] font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-sm transition">Switch View</button>
    </div>
  </div>
</header>

<main class="flex-1 max-w-[1440px] w-full mx-auto px-4 md:px-6 py-4 space-y-3.5">

<!-- ========== AUTONOMOUS AGENT LOOP ALERT BANNER ========== -->
<section id="loop-alert-banner" class="hidden card px-4 py-3 border-rose-500/50 bg-gradient-to-r from-rose-950/50 via-surface-900 to-surface-900 flex flex-wrap items-center justify-between gap-3 shadow-lg shadow-rose-950/20 fade-in">
  <div class="flex items-center gap-3">
    <div class="h-9 w-9 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center text-lg border border-rose-500/30">⚠️</div>
    <div>
      <div class="flex items-center gap-2">
        <span class="text-xs font-bold text-rose-200 uppercase tracking-wide">Autonomous Agent Loop Detected</span>
        <span id="loop-alert-badge" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-rose-950 text-rose-400 border border-rose-800">WARNING</span>
      </div>
      <p id="loop-alert-msg" class="text-[11px] text-slate-300 mt-0.5">High retry frequency detected on task with repeated failures.</p>
    </div>
  </div>
  <div class="flex items-center gap-2">
    <button id="loop-inspect-btn" onclick="inspectStuckTask()" class="px-3 py-1.5 text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white rounded-lg transition shadow-sm flex items-center gap-1.5">
      <span>🔍 Inspect Stuck Task</span>
    </button>
  </div>
</section>

<!-- ========== DEVELOPER PROFILE BANNER ========== -->
<section id="developer-banner" class="hidden card px-3.5 py-2 flex flex-wrap items-center justify-between gap-2.5 border-indigo-900/30 bg-gradient-to-r from-surface-900 to-indigo-950/20 fade-in">
  <div class="flex items-center gap-2.5">
    <div class="h-8 w-8 rounded-lg bg-indigo-500/15 text-indigo-400 flex items-center justify-center text-sm border border-indigo-500/25">👤</div>
    <div>
      <p class="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Personal Developer Workspace</p>
      <div class="flex items-center gap-2 mt-0.5">
        <span class="text-xs font-bold text-white leading-tight" id="banner-user-name">dev</span>
        <span class="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/70 text-emerald-400 border border-emerald-800/60">🔒 Isolated View — Private Metrics</span>
      </div>
    </div>
  </div>
  <div class="flex items-center gap-2.5 text-[10px]">
    <div class="bg-surface-950/60 px-2.5 py-1 rounded-md border border-surface-700/70 flex items-center gap-2">
      <div><span class="text-slate-400 text-[10px]">Daily Quota:</span> <span id="banner-quota-text" class="text-[10px] font-bold text-cyan-400 ml-0.5">0%</span></div>
      <div class="w-16 h-1.5 bg-surface-800 rounded-full overflow-hidden">
        <div id="banner-quota-bar" class="h-full bg-cyan-400 transition-all duration-300" style="width: 0%"></div>
      </div>
    </div>
    <div class="bg-surface-950/60 px-2.5 py-1 rounded-md border border-surface-700/70"><span class="text-slate-400">Key:</span> <span id="banner-masked-key" class="mono text-cyan-400 font-semibold ml-0.5">•••</span></div>
    <div class="bg-surface-950/60 px-2.5 py-1 rounded-md border border-surface-700/70"><span class="text-slate-400">Provider:</span> <span id="banner-provider" class="uppercase font-semibold text-slate-200 ml-0.5">—</span></div>
  </div>
</section>

<!-- ========== METRICS GRID ========== -->
<section class="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
  <div class="card card-glow px-3.5 py-2.5 metric-gradient-1">
    <span class="text-[10px] text-indigo-300/80 uppercase tracking-wider font-bold">Total Calls</span>
    <p id="total-calls" class="text-xl font-bold text-white mt-0.5">—</p>
    <span id="total-calls-sub" class="text-[10px] text-slate-500">Proxied traces</span>
  </div>
  <div class="card card-glow px-3.5 py-2.5 metric-gradient-2">
    <span class="text-[10px] text-cyan-300/80 uppercase tracking-wider font-bold">Avg Latency</span>
    <p id="avg-latency" class="text-xl font-bold text-cyan-400 mt-0.5">—</p>
    <span class="text-[10px] text-slate-500">Ms / call</span>
  </div>
  <div class="card card-glow px-3.5 py-2.5 metric-gradient-3">
    <span class="text-[10px] text-emerald-300/80 uppercase tracking-wider font-bold">Total Tokens</span>
    <p id="total-tokens" class="text-xl font-bold text-emerald-400 mt-0.5">—</p>
    <span id="token-split" class="text-[10px] text-slate-500">In: — | Out: —</span>
  </div>
  <div class="card card-glow px-3.5 py-2.5 metric-gradient-4">
    <span class="text-[10px] text-amber-300/80 uppercase tracking-wider font-bold">Est. Cost</span>
    <p id="est-cost" class="text-xl font-bold text-amber-400 mt-0.5">—</p>
    <span id="cost-detail" class="text-[10px] text-slate-500">Public pricing</span>
  </div>
</section>

<!-- ========== TAB NAVIGATION ========== -->
<nav class="flex flex-wrap gap-1 bg-surface-950 p-1 rounded-xl border border-surface-700/70 text-[11px]">
  <button onclick="switchTab('overview')"   id="tab-overview"   class="tab-active   px-3.5 py-1.5 font-semibold rounded-lg transition-all">📊 Overview</button>
  <button onclick="switchTab('traces')"     id="tab-traces"     class="tab-inactive px-3.5 py-1.5 font-semibold rounded-lg transition-all">🔍 Trace Explorer</button>
  <button onclick="switchTab('export')"     id="tab-export"     class="tab-inactive px-3.5 py-1.5 font-semibold rounded-lg transition-all" style="display:none">📦 Dataset Export</button>
  <button onclick="switchTab('setup')"      id="tab-setup"      class="tab-inactive px-3.5 py-1.5 font-semibold rounded-lg transition-all">⚡ IDE Setup</button>
  <button onclick="switchTab('compare')"    id="tab-compare"    class="tab-inactive px-3.5 py-1.5 font-semibold rounded-lg transition-all">🏆 Compare Models</button>
</nav>

<!-- ====================== TAB: OVERVIEW ====================== -->
<div id="panel-overview" class="space-y-3.5 fade-in">

  <!-- ADMIN: Connected Developers -->
  <section id="admin-developers-section" class="hidden card overflow-hidden">
    <div class="px-4 py-2.5 border-b border-surface-700 flex flex-wrap justify-between items-center gap-2 bg-surface-950/50">
      <div>
        <h2 class="text-xs font-bold text-violet-400 uppercase tracking-wider flex items-center gap-1.5">👑 Connected Developers</h2>
        <p class="text-[10px] text-slate-500 mt-0.5">Developers who routed API keys through this Observer instance</p>
      </div>
      <span id="connected-count" class="text-[10px] px-2 py-0.5 rounded-full bg-violet-950/60 text-violet-300 border border-violet-800/50 font-bold">0 developers</span>
    </div>
    <div class="overflow-x-auto"><table class="w-full text-left text-xs text-slate-300"><thead class="bg-surface-950/70 text-[10px] text-slate-500 border-b border-surface-700 uppercase">
      <tr><th class="py-2 px-3.5">Developer</th><th class="py-2 px-3.5">Project</th><th class="py-2 px-3.5">API Key</th><th class="py-2 px-3.5">Provider</th><th class="py-2 px-3.5">Models</th><th class="py-2 px-3.5">Calls</th><th class="py-2 px-3.5">Tokens</th><th class="py-2 px-3.5">Last Active</th><th class="py-2 px-3.5"></th></tr>
    </thead><tbody id="developers-body" class="divide-y divide-surface-700"><tr><td colspan="9" class="py-4 text-center text-slate-600 text-xs">Loading...</td></tr></tbody></table></div>
  </section>

  <!-- Sleek Compact Analytics Widget with Graph Tabs -->
  <section class="card overflow-hidden border border-surface-700/80">
    <div class="px-3.5 py-2 border-b border-surface-700/60 bg-surface-950/60 flex flex-wrap justify-between items-center gap-2">
      <div class="flex items-center gap-2.5">
        <!-- Sub-tabs for Graph Mode -->
        <div class="inline-flex p-0.5 rounded-lg bg-surface-900 border border-surface-700/70 text-[10px]">
          <button id="graph-tab-activity" onclick="switchGraphMode('activity')" class="px-2.5 py-1 rounded-md font-bold text-white bg-indigo-600 transition">📈 Calls Activity</button>
          <button id="graph-tab-tokens"   onclick="switchGraphMode('tokens')"   class="px-2.5 py-1 rounded-md font-semibold text-slate-400 hover:text-white transition">🪙 Tokens</button>
          <button id="graph-tab-split"    onclick="switchGraphMode('split')"    class="px-2 py-1 rounded-md font-semibold text-slate-400 hover:text-white transition hidden md:inline">⊞ Both</button>
        </div>
        <span id="chart-summary-text" class="text-[10px] text-slate-400 hidden sm:inline">Daily calls volume</span>
      </div>
      <div class="flex items-center gap-2">
        <!-- Range Selector Pills -->
        <div class="inline-flex p-0.5 rounded-lg bg-surface-900 border border-surface-700/70 text-[10px] font-semibold">
          <button onclick="setChartRange(7)"  id="range-7"  class="px-2 py-0.5 rounded text-indigo-300 bg-surface-800 transition font-bold">7D</button>
          <button onclick="setChartRange(14)" id="range-14" class="px-2 py-0.5 rounded text-slate-400 hover:text-white transition">14D</button>
          <button onclick="setChartRange(30)" id="range-30" class="px-2 py-0.5 rounded text-slate-400 hover:text-white transition">30D</button>
        </div>
        <!-- Collapse/Expand Toggle -->
        <button onclick="toggleChartCollapse()" id="chart-collapse-btn" title="Toggle Graph Visibility" class="text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-surface-800 text-[10px] border border-surface-700/50 transition flex items-center gap-1">
          <span id="chart-collapse-icon">▾</span>
          <span id="chart-collapse-label">Fold</span>
        </button>
      </div>
    </div>
    
    <!-- Collapsible Chart Body with Fixed Compact Height -->
    <div id="chart-container-body" class="p-3 transition-all duration-200">
      <div id="charts-grid" class="grid grid-cols-1 gap-2">
        <div id="wrapper-activity" class="relative h-36 w-full">
          <canvas id="chart-activity"></canvas>
        </div>
        <div id="wrapper-tokens" class="relative h-36 w-full hidden">
          <canvas id="chart-tokens"></canvas>
        </div>
      </div>
    </div>
  </section>

  <!-- Model Leaderboard -->
  <section class="card overflow-hidden">
    <div class="px-4 py-2.5 border-b border-surface-700 bg-surface-950/50 flex justify-between items-center">
      <div><h2 class="text-xs font-bold text-slate-200 uppercase tracking-wider">Model Performance Leaderboard</h2>
      <p id="leaderboard-sub" class="text-[10px] text-slate-500 mt-0.5">Last-touch outcome attribution</p></div>
      <span id="active-filter" class="text-[11px] text-indigo-400 font-medium cursor-pointer"></span>
    </div>
    <div class="overflow-x-auto"><table class="w-full text-left text-xs text-slate-300"><thead class="bg-surface-950/70 text-[10px] text-slate-500 border-b border-surface-700 uppercase">
      <tr><th class="py-2 px-3.5">Model</th><th class="py-2 px-3.5">Calls</th><th class="py-2 px-3.5">Avg Latency</th><th class="py-2 px-3.5">In Tokens</th><th class="py-2 px-3.5">Out Tokens</th><th class="py-2 px-3.5">Pass / Fail</th><th class="py-2 px-3.5">Success</th><th class="py-2 px-3.5">Est. Cost</th></tr>
    </thead><tbody id="models-body" class="divide-y divide-surface-700"><tr><td colspan="8" class="py-4 text-center text-slate-600 text-xs">Loading...</td></tr></tbody></table></div>
  </section>
</div>

<!-- ====================== TAB: TRACE EXPLORER ====================== -->
<div id="panel-traces" class="hidden space-y-4 fade-in">
  <section class="card overflow-hidden">
    <div class="p-4 border-b border-surface-700 bg-surface-950/50">
      <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider">🔍 Recent Tasks & Trace Inspector</h2>
      <p class="text-[11px] text-slate-500 mt-0.5">Click any task row to inspect the full trace — prompts, responses, tool calls, and outcomes</p>
    </div>
    <div class="overflow-x-auto"><table class="w-full text-left text-[13px] text-slate-300"><thead class="bg-surface-950/70 text-[10px] text-slate-500 border-b border-surface-700 uppercase">
      <tr><th class="py-2.5 px-4">Task ID</th><th class="py-2.5 px-4">Project</th><th class="py-2.5 px-4">Type</th><th class="py-2.5 px-4">Calls</th><th class="py-2.5 px-4">Model</th><th class="py-2.5 px-4">Outcome</th><th class="py-2.5 px-4">Created</th></tr>
    </thead><tbody id="tasks-body" class="divide-y divide-surface-700"><tr><td colspan="7" class="py-6 text-center text-slate-600 text-xs">Loading...</td></tr></tbody></table></div>
  </section>
</div>

<!-- ========== TRACE INSPECTOR SLIDE-OVER ========== -->
<div id="trace-panel" class="fixed inset-0 z-50 hidden">
  <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeTracePanel()"></div>
  <div class="absolute right-0 top-0 bottom-0 w-full max-w-2xl bg-surface-900 border-l border-surface-700 overflow-y-auto slide-enter">
    <div class="sticky top-0 z-10 glass border-b border-surface-700 p-4 flex justify-between items-center">
      <div><h3 class="text-sm font-bold text-white">Trace Inspector</h3><p id="trace-task-id" class="mono text-[11px] text-indigo-400 mt-0.5"></p></div>
      <button onclick="closeTracePanel()" class="h-8 w-8 rounded-lg bg-surface-800 hover:bg-surface-700 text-slate-400 hover:text-white flex items-center justify-center text-lg transition">&times;</button>
    </div>
    <div id="trace-content" class="p-4 space-y-4"></div>
  </div>
</div>

<!-- ====================== TAB: DATASET EXPORT ====================== -->
<div id="panel-export" class="hidden space-y-4 fade-in">
  <section class="card p-6 space-y-5">
    <div>
      <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">📦 Training Dataset Export</h2>
      <p class="text-[11px] text-slate-500 mt-1">Generate fine-tuning datasets from verified task telemetry. Only tasks with pass/accepted outcomes are included.</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label class="block text-[11px] font-bold text-slate-400 uppercase mb-1.5">Format</label>
        <div class="flex gap-2">
          <button id="btn-sft" onclick="setExportType('sft')" class="flex-1 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white border border-indigo-500 transition">SFT</button>
          <button id="btn-dpo" onclick="setExportType('dpo')" class="flex-1 py-2 rounded-lg text-xs font-bold bg-surface-800 text-slate-400 border border-surface-700 transition">DPO</button>
        </div>
        <p id="export-type-desc" class="text-[10px] text-slate-500 mt-1.5">Supervised Fine-Tuning — ShareGPT format with verified prompt→response pairs.</p>
      </div>
      <div>
        <label class="block text-[11px] font-bold text-slate-400 uppercase mb-1.5">Project Filter</label>
        <input id="export-project" type="text" placeholder="All projects" class="w-full px-3 py-2 text-xs bg-surface-800 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
      </div>
      <div>
        <label class="block text-[11px] font-bold text-slate-400 uppercase mb-1.5">Max Records</label>
        <input id="export-limit" type="number" value="500" min="10" max="10000" class="w-full px-3 py-2 text-xs bg-surface-800 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
      </div>
    </div>
    <div class="flex items-center gap-4">
      <button onclick="runExport()" id="export-run-btn" class="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition">Generate & Download .jsonl</button>
      <span id="export-status" class="text-[11px] text-slate-500"></span>
    </div>
    <div id="export-preview" class="hidden card p-4 bg-surface-950 border-indigo-900/30 space-y-2">
      <h4 class="text-xs font-bold text-indigo-400 uppercase">Export Summary</h4>
      <div id="export-summary-content" class="text-xs text-slate-300 space-y-1"></div>
    </div>
  </section>

  <!-- Specialist Model Retraining Center (Phase 6) -->
  <section class="card p-6 space-y-5 border border-indigo-900/40 bg-gradient-to-br from-surface-900 to-indigo-950/20">
    <div>
      <h2 class="text-sm font-bold text-violet-300 uppercase tracking-wider flex items-center gap-2">🚀 Specialist Model Retraining Center</h2>
      <p class="text-[11px] text-slate-400 mt-1">Launch cloud/local fine-tuning runs for Observer specialist models using verified telemetry.</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div>
        <label class="block text-[11px] font-bold text-slate-400 uppercase mb-1.5">Specialist Model</label>
        <select id="retrain-model" class="w-full px-3 py-2 text-xs bg-surface-800 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
          <option value="Qwen/Qwen2.5-Coder-1.5B">Fast Coder (Qwen2.5-Coder-1.5B)</option>
          <option value="Qwen/Qwen2.5-Coder-7B">Heavy Coder (Qwen2.5-Coder-7B)</option>
          <option value="deepseek-ai/DeepSeek-R1">Deep Reasoner (DeepSeek-R1)</option>
          <option value="Qwen/Qwen2.5-Math-7B">Math Specialist (Qwen2.5-Math-7B)</option>
          <option value="Qwen/Qwen2-VL-7B-Instruct">Vision Specialist (Qwen2-VL-7B)</option>
        </select>
      </div>
      <div>
        <label class="block text-[11px] font-bold text-slate-400 uppercase mb-1.5">Training Objective</label>
        <select id="retrain-dataset-type" class="w-full px-3 py-2 text-xs bg-surface-800 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
          <option value="sft">Supervised Fine-Tuning (SFT)</option>
          <option value="dpo">Direct Preference Optimization (DPO)</option>
        </select>
      </div>
      <div>
        <label class="block text-[11px] font-bold text-slate-400 uppercase mb-1.5">LoRA Rank (r)</label>
        <select id="retrain-rank" class="w-full px-3 py-2 text-xs bg-surface-800 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
          <option value="16">Rank 16 (Alpha 32)</option>
          <option value="32">Rank 32 (Alpha 64)</option>
          <option value="64">Rank 64 (Alpha 128)</option>
        </select>
      </div>
      <div>
        <label class="block text-[11px] font-bold text-slate-400 uppercase mb-1.5">Epochs</label>
        <input id="retrain-epochs" type="number" value="3" min="1" max="10" class="w-full px-3 py-2 text-xs bg-surface-800 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
      </div>
    </div>
    <div class="flex items-center gap-4">
      <button onclick="triggerRetraining()" id="retrain-run-btn" class="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-violet-500/20 transition flex items-center gap-2">
        <span id="retrain-spinner" class="hidden h-3 w-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
        <span>🚀 Launch Retraining Run</span>
      </button>
      <span id="retrain-status-text" class="text-xs text-slate-400"></span>
    </div>
    <!-- Terminal Output Drawer -->
    <div id="retrain-console" class="hidden bg-surface-950 border border-surface-800 rounded-xl p-3.5 space-y-2 mono text-xs">
      <div class="flex items-center justify-between text-slate-400 text-[11px] border-b border-surface-800/80 pb-2">
        <span class="flex items-center gap-1.5"><span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span> Cloud GPU Execution Console</span>
        <span id="retrain-job-id" class="text-indigo-400 font-bold"></span>
      </div>
      <div class="w-full bg-surface-800 rounded-full h-1.5 overflow-hidden">
        <div id="retrain-progress-bar" class="bg-gradient-to-r from-indigo-500 to-violet-500 h-1.5 transition-all duration-300" style="width: 0%"></div>
      </div>
      <div id="retrain-log-output" class="text-slate-300 text-[11px] max-h-48 overflow-y-auto space-y-1 py-1"></div>
    </div>
  </section>
</div>

<!-- ====================== TAB: IDE SETUP ====================== -->
<div id="panel-setup" class="hidden fade-in">
  <div class="card p-6 space-y-5">
    <div>
      <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider">⚡ One-Click IDE Setup</h2>
      <p class="text-[11px] text-slate-500 mt-1">Copy the configuration snippet for your editor and start routing all LLM calls through Observer in 10 seconds.</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="ide-cards"></div>
  </div>
</div>

<!-- ====================== TAB: MODEL COMPARE ====================== -->
<div id="panel-compare" class="hidden fade-in">
  <section class="card p-6 space-y-5">
    <div>
      <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider">🏆 Model Comparison</h2>
      <p class="text-[11px] text-slate-500 mt-1">Side-by-side comparison of real-world performance across models observed in production.</p>
    </div>
    <div id="compare-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
    <div class="card p-4 bg-surface-950 border-indigo-900/30">
      <h4 class="text-xs font-bold text-indigo-400 uppercase mb-2">Recommendation</h4>
      <p id="compare-recommendation" class="text-xs text-slate-300">Collecting performance data...</p>
    </div>
  </section>
</div>

</main>

<footer class="border-t border-surface-700 px-6 py-3 text-center text-[10px] text-slate-600">AI Model Observer &bull; Role-Based Analytics Dashboard &bull; Auto-refresh 8s</footer>

<!-- ========== ACCESS MODAL ========== -->
<div id="access-modal" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden items-center justify-center p-4 z-50">
  <div class="bg-surface-900 border border-surface-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 fade-in">
    <div class="flex items-center justify-between border-b border-surface-700 pb-3">
      <h3 class="font-bold text-white text-sm">Select Dashboard View</h3>
      <button onclick="closeAccessModal()" class="text-slate-400 hover:text-white text-lg">&times;</button>
    </div>
    <div class="grid grid-cols-2 gap-2 bg-surface-950 p-1 rounded-lg border border-surface-700 text-[11px] font-bold">
      <button id="tab-btn-dev" onclick="switchModalTab('dev')" class="py-2 rounded-md bg-indigo-600 text-white transition">👤 Developer</button>
      <button id="tab-btn-admin" onclick="switchModalTab('admin')" class="py-2 rounded-md text-slate-400 hover:text-white transition">👑 Admin</button>
    </div>
    <div id="modal-tab-dev" class="space-y-3">
      <p class="text-[11px] text-slate-400">Log in with your developer name. You will view <strong>strictly your own</strong> personal metrics, private traces, and masked API key. Other users cannot see your data, and you cannot see theirs.</p>
      <input id="modal-input-user" type="text" placeholder="Your developer name (e.g. alex)" class="w-full px-3 py-2 text-xs bg-surface-950 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
      <button onclick="submitDeveloperLogin()" class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 font-bold text-[11px] text-white rounded-lg transition shadow-md">Enter Personal Dashboard</button>
    </div>
    <div id="modal-tab-admin" class="space-y-3 hidden">
      <p class="text-[11px] text-slate-400">Log in with administrator key. Grants <strong>full global team visibility</strong> across all connected developers, total token consumption, system-wide task traces, and dataset curation exports.</p>
      <input id="modal-input-admin-key" type="password" placeholder="Enter OBSERVER_ADMIN_KEY" class="w-full px-3 py-2 text-xs bg-surface-950 border border-surface-700 rounded-lg text-white focus:outline-none focus:border-indigo-500">
      <button onclick="submitAdminLogin()" class="w-full py-2.5 bg-violet-600 hover:bg-violet-500 font-bold text-[11px] text-white rounded-lg transition shadow-md">Unlock Admin Dashboard</button>
    </div>
  </div>
</div>

<script>
// ────────── State ──────────
const P = new URLSearchParams(location.search);
let S = {
  role: 'guest',
  user: P.get('user') || localStorage.getItem('ao_user') || '',
  adminToken: P.get('admin_token') || P.get('token') || localStorage.getItem('ao_admin_token') || '',
  filterUser: null,
  exportType: 'sft',
  statsCache: [],
  ws: null,
  stuckTaskId: null,
  retrainPollTimer: null,
};
let activityChart = null, tokenChart = null;

// ────────── Cost Lookup (per 1M tokens) ──────────
const COST = {
  'gemini-3.1-flash-lite': { i: 0.075, o: 0.30 },
  'gemini-3.8-flash': { i: 0.15, o: 0.60 },
  'gemini-2.5-flash': { i: 0.15, o: 0.60 },
  'gemini-2.5-pro': { i: 1.25, o: 5.00 },
  'claude-3-5-sonnet': { i: 3.00, o: 15.00 },
  'claude-3-opus': { i: 15.00, o: 75.00 },
  'claude-sonnet-4': { i: 3.00, o: 15.00 },
  'gpt-4o': { i: 2.50, o: 10.00 },
  'gpt-4o-mini': { i: 0.15, o: 0.60 },
  'deepseek-chat': { i: 0.27, o: 1.10 },
  'deepseek-coder': { i: 0.14, o: 0.28 },
  '_default': { i: 0.50, o: 2.00 },
};
function estimateCost(model, inTok, outTok) {
  let key = Object.keys(COST).find(k => model.toLowerCase().includes(k));
  let r = COST[key] || COST['_default'];
  return ((inTok||0) * r.i + (outTok||0) * r.o) / 1_000_000;
}
function fmtCost(v) { return v < 0.01 ? '<$0.01' : '$' + v.toFixed(2); }

// ────────── Init ──────────
function initAuth() {
  if (S.adminToken) S.role = 'admin';
  else if (S.user) S.role = 'dev';
  else { S.role = 'dev'; S.user = 'dev'; }
  updateUIForRole();
}
function updateUIForRole() {
  const badge = document.getElementById('role-badge');
  const banner = document.getElementById('developer-banner');
  const adminSec = document.getElementById('admin-developers-section');
  const exportTab = document.getElementById('tab-export');
  if (S.role === 'admin') {
    badge.className = "px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-violet-950/60 text-violet-300 border border-violet-800/50 flex items-center gap-1";
    badge.textContent = "👑 Admin (Global View)";
    banner.classList.add('hidden');
    adminSec.classList.remove('hidden');
    exportTab.style.display = '';
  } else {
    badge.className = "px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-cyan-950/60 text-cyan-300 border border-cyan-800/50 flex items-center gap-1";
    badge.innerHTML = "👤 Developer: " + S.user + " <span class='text-[9px] text-cyan-400 font-normal'>(Private View)</span>";
    banner.classList.remove('hidden');
    adminSec.classList.add('hidden');
    exportTab.style.display = 'none';
    if (document.getElementById('panel-export') && !document.getElementById('panel-export').classList.contains('hidden')) {
      switchTab('overview');
    }
    document.getElementById('banner-user-name').textContent = S.user;
  }
}

// ────────── Tabs ──────────
const TABS = ['overview','traces','export','setup','compare'];
function switchTab(t) {
  TABS.forEach(id => {
    document.getElementById('panel-'+id).classList.toggle('hidden', id !== t);
    const btn = document.getElementById('tab-'+id);
    btn.className = id === t ? 'tab-active px-3.5 py-1.5 font-semibold rounded-lg transition-all' : 'tab-inactive px-3.5 py-1.5 font-semibold rounded-lg transition-all';
    if (id === 'export' && S.role !== 'admin') btn.style.display = 'none';
  });
  if (t === 'setup') renderIDECards();
  if (t === 'compare') renderCompare();
  if (t === 'overview') { setTimeout(() => fetchTimeseries(), 100); }
}

// ────────── Fetch Data ──────────
function authHeaders() {
  let h = {};
  if (S.adminToken) {
    h['X-Admin-Token'] = S.adminToken;
    h['Authorization'] = 'Bearer ' + S.adminToken;
  } else if (S.user) {
    h['X-Session-Id'] = S.user;
  }
  return h;
}
async function fetchData() {
  try {
    let hD = { ok: false, status: 'offline' };
    try {
      const hRes = await fetch('/health');
      if (hRes.ok) hD = await hRes.json();
    } catch(err) {}
    const hBadge = document.getElementById('health-badge');
    if (hD.ok && hD.status === 'ready') {
      hBadge.className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/50";
      hBadge.innerHTML='<span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>Online';
    } else {
      hBadge.className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/50";
      hBadge.innerHTML='<span class="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse"></span>DB Connecting';
    }

    let sq = '', tq = '', h = authHeaders();
    if (S.role === 'admin') {
      if (S.filterUser) { sq = '?session_id='+encodeURIComponent(S.filterUser); tq = '?session_id='+encodeURIComponent(S.filterUser); document.getElementById('active-filter').textContent = '✕ Filter: '+S.filterUser; document.getElementById('active-filter').onclick = () => { S.filterUser=null; fetchData(); }; }
      else { document.getElementById('active-filter').textContent=''; }
      fetchAdminDevelopers(h);
    } else {
      sq = '?session_id='+encodeURIComponent(S.user);
      tq = '?session_id='+encodeURIComponent(S.user);
      fetchUserProfile(S.user);
    }
    const sRes = await fetch('/stats'+sq, {headers:h});
    if (sRes.ok) {
      S.statsCache = await sRes.json();
      renderStats(S.statsCache);
    } else if (sRes.status === 503) {
      const mb = document.getElementById('models-body');
      if (mb) mb.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-amber-400 text-xs">⚠️ Database is connecting. Run <code class="mono bg-surface-900 px-2 py-0.5 rounded border border-surface-700 text-cyan-300">docker compose up -d db</code> in terminal.</td></tr>';
    }
    const tRes = await fetch('/tasks'+tq, {headers:h});
    if (tRes.ok) {
      renderTasks(await tRes.json());
    } else if (tRes.status === 503) {
      const tb = document.getElementById('tasks-body');
      if (tb) tb.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-amber-400 text-xs">⚠️ Database is connecting. Run <code class="mono bg-surface-900 px-2 py-0.5 rounded border border-surface-700 text-cyan-300">docker compose up -d db</code> in terminal.</td></tr>';
    }
    fetchTimeseries();
  } catch(e) { console.error('Refresh:', e); }
}

async function fetchAdminDevelopers(h) {
  try { const r = await fetch('/admin/connected-users',{headers:h}); if (r.ok) { const d = await r.json(); renderDevelopers(d.users||[]); } } catch(e) {}
}
async function fetchUserProfile(u) {
  try { const r = await fetch('/user/profile?user='+encodeURIComponent(u), {headers:authHeaders()}); if (r.ok) { const d = await r.json(); const p=d.profile||{}; document.getElementById('banner-masked-key').textContent=p.key_masked||'—'; document.getElementById('banner-provider').textContent=(p.provider||'—').toUpperCase(); } } catch(e) {}
}
let currentChartDays = 7;
let currentGraphMode = 'activity';
let chartCollapsed = false;

async function fetchTimeseries() {
  const days = currentChartDays || 7;
  let q = '?days='+days;
  if (S.role !== 'admin') q += '&session_id='+encodeURIComponent(S.user);
  else if (S.filterUser) q += '&session_id='+encodeURIComponent(S.filterUser);
  try {
    const r = await fetch('/stats/timeseries'+q, {headers:authHeaders()});
    if (r.ok) { const d = await r.json(); renderCharts(d.series||[], parseInt(days)); }
  } catch(e) { console.warn('Timeseries:', e); }
}

// ────────── Render: Developers ──────────
function renderDevelopers(devs) {
  const tb = document.getElementById('developers-body');
  document.getElementById('connected-count').textContent = devs.length + ' developer' + (devs.length===1?'':'s');
  if (!devs.length) { tb.innerHTML='<tr><td colspan="9" class="py-6 text-center text-slate-600 text-xs">No developers connected yet.</td></tr>'; return; }
  tb.innerHTML='';
  devs.forEach(d => {
    const models = (d.models_used||[]).map(m=>'<span class="px-1.5 py-0.5 rounded bg-surface-800 text-[10px] mono border border-surface-700">'+m+'</span>').join(' ')||'—';
    const tr = document.createElement('tr'); tr.className='hover:bg-surface-800/40 transition cursor-pointer';
    tr.innerHTML = `<td class="py-2.5 px-4 font-semibold text-white text-xs flex items-center gap-2"><span class="h-6 w-6 rounded-full bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center text-[10px] font-bold">${(d.session_id||'?')[0].toUpperCase()}</span>${d.session_id}</td>
    <td class="py-2.5 px-4 text-[11px] text-slate-500 mono">${d.project||'—'}</td>
    <td class="py-2.5 px-4 mono text-cyan-400 text-[11px] font-bold">${d.key_masked}</td>
    <td class="py-2.5 px-4 text-[11px] uppercase font-semibold text-slate-400">${d.provider||'—'}</td>
    <td class="py-2.5 px-4 text-[11px]">${models}</td>
    <td class="py-2.5 px-4 font-bold text-slate-200 text-xs">${(d.total_calls||0).toLocaleString()}</td>
    <td class="py-2.5 px-4 text-[11px] text-slate-500">${((d.total_input_tokens||0)+(d.total_output_tokens||0)).toLocaleString()}</td>
    <td class="py-2.5 px-4 text-[11px] text-slate-500">${d.last_seen?new Date(d.last_seen).toLocaleString():'-'}</td>
    <td class="py-2.5 px-4"><button onclick="event.stopPropagation();S.filterUser='${d.session_id}';fetchData()" class="px-2 py-1 bg-surface-800 hover:bg-surface-700 text-indigo-300 rounded text-[10px] font-bold border border-surface-700 transition">Inspect</button></td>`;
    tb.appendChild(tr);
  });
}

// ────────── Render: Stats ──────────
function renderStats(stats) {
  let tc=0,ti=0,to=0,tp=0,tf=0,tl=0,totalCost=0;
  const tb=document.getElementById('models-body');
  if(!stats||!stats.length){tb.innerHTML='<tr><td colspan="8" class="py-6 text-center text-slate-600 text-xs">No data.</td></tr>';['total-calls','avg-latency','total-tokens','est-cost'].forEach(id=>document.getElementById(id).textContent='—');return;}
  tb.innerHTML='';
  stats.forEach(m=>{
    tc+=m.calls||0; ti+=m.input_tokens||0; to+=m.output_tokens||0; tp+=m.passes||0; tf+=m.fails||0; tl+=(m.avg_latency_ms||0)*(m.calls||0);
    const cost=estimateCost(m.model,m.input_tokens,m.output_tokens); totalCost+=cost;
    const ot=(m.passes||0)+(m.fails||0); const rate=ot>0?Math.round((m.passes/ot)*100):null;
    const rc=rate>=70?'text-emerald-400':rate>=40?'text-amber-400':'text-slate-500';
    const tr=document.createElement('tr'); tr.className='hover:bg-surface-800/40 transition';
    tr.innerHTML=`<td class="py-2.5 px-4 mono font-semibold text-slate-200 text-xs">${m.model}</td>
    <td class="py-2.5 px-4 font-bold text-white">${(m.calls||0).toLocaleString()}</td>
    <td class="py-2.5 px-4 text-slate-400 text-xs">${m.avg_latency_ms?m.avg_latency_ms+'ms':'—'}</td>
    <td class="py-2.5 px-4 text-slate-500 text-[11px]">${(m.input_tokens||0).toLocaleString()}</td>
    <td class="py-2.5 px-4 text-slate-500 text-[11px]">${(m.output_tokens||0).toLocaleString()}</td>
    <td class="py-2.5 px-4 text-xs"><span class="text-emerald-400 font-bold">${m.passes||0}</span><span class="text-slate-600 mx-0.5">/</span><span class="text-rose-400 font-bold">${m.fails||0}</span></td>
    <td class="py-2.5 px-4 font-bold ${rc}">${rate!==null?rate+'%':'—'}</td>
    <td class="py-2.5 px-4 text-amber-400/70 text-[11px] font-semibold">${fmtCost(cost)}</td>`;
    tb.appendChild(tr);
  });
  document.getElementById('total-calls').textContent=tc.toLocaleString();
  document.getElementById('avg-latency').textContent=tc>0?Math.round(tl/tc)+'ms':'—';
  document.getElementById('total-tokens').textContent=(ti+to).toLocaleString();
  document.getElementById('token-split').textContent='In: '+ti.toLocaleString()+' | Out: '+to.toLocaleString();
  document.getElementById('est-cost').textContent=fmtCost(totalCost);
}

// ────────── Render: Tasks ──────────
function renderTasks(tasks) {
  const tb=document.getElementById('tasks-body');
  if(!tasks||!tasks.length){tb.innerHTML='<tr><td colspan="7" class="py-6 text-center text-slate-600 text-xs">No tasks.</td></tr>';return;}
  tb.innerHTML='';
  tasks.forEach(t=>{
    let bc='bg-surface-800 text-slate-400 border-surface-700',st=t.latest_outcome||'running';
    if(['pass','accepted'].includes(t.latest_outcome)){bc='bg-emerald-950/60 text-emerald-400 border-emerald-800/50';}
    else if(['fail','rejected'].includes(t.latest_outcome)){bc='bg-rose-950/60 text-rose-400 border-rose-800/50';}
    else if(t.latest_outcome==='edited'){bc='bg-amber-950/60 text-amber-400 border-amber-800/50';}
    const tr=document.createElement('tr'); tr.className='hover:bg-surface-800/40 transition cursor-pointer'; tr.onclick=()=>openTracePanel(t.task_id);
    tr.innerHTML=`<td class="py-2.5 px-4 mono text-xs font-bold text-indigo-300">${t.task_id}</td>
    <td class="py-2.5 px-4 text-[11px] text-slate-500">${t.project||'—'}</td>
    <td class="py-2.5 px-4 text-[11px] text-slate-500">${t.task_type||'—'}</td>
    <td class="py-2.5 px-4 text-xs font-bold text-slate-200">${t.call_count||0}</td>
    <td class="py-2.5 px-4 mono text-[11px] text-slate-300">${t.primary_model||'—'}</td>
    <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${bc}">${st}</span></td>
    <td class="py-2.5 px-4 text-[11px] text-slate-500">${t.created_at?new Date(t.created_at).toLocaleString():'-'}</td>`;
    tb.appendChild(tr);
  });
}

// ────────── Trace Inspector ──────────
async function openTracePanel(taskId) {
  document.getElementById('trace-panel').classList.remove('hidden');
  document.getElementById('trace-task-id').textContent = taskId;
  const content = document.getElementById('trace-content');
  content.innerHTML = '<p class="text-xs text-slate-500 animate-pulse">Loading trace data...</p>';
  try {
    const r = await fetch('/tasks/'+encodeURIComponent(taskId), {headers:authHeaders()});
    if (!r.ok) {
      const err = r.status === 403 ? '🔒 Access Forbidden: this trace belongs to another developer.' : 'Failed to load trace.';
      content.innerHTML = `<div class="p-3 bg-rose-950/40 border border-rose-800/50 rounded-lg text-rose-300 text-xs">${err}</div>`;
      return;
    }
    const d = await r.json();
    let html = '';
    // Task Info
    const tk = d.task||{};
    html += `<div class="card p-3 space-y-1"><h4 class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Task Details</h4>
    <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
      <div><span class="text-slate-500">Project:</span> <span class="text-white font-semibold">${tk.project||'—'}</span></div>
      <div><span class="text-slate-500">Type:</span> <span class="text-white font-semibold">${tk.task_type||'—'}</span></div>
      <div><span class="text-slate-500">Title:</span> <span class="text-white font-semibold">${tk.title||'—'}</span></div>
      <div><span class="text-slate-500">Created:</span> <span class="text-white">${tk.created_at?new Date(tk.created_at).toLocaleString():'—'}</span></div>
    </div></div>`;
    // Outcomes
    if (d.outcomes && d.outcomes.length) {
      html += '<div class="card p-3 space-y-2"><h4 class="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Outcomes & Signals</h4>';
      d.outcomes.forEach(o => {
        let oc = o.status==='pass'||o.status==='accepted' ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40' : 'text-rose-400 bg-rose-950/40 border-rose-800/40';
        html += `<div class="flex items-start gap-2 p-2 rounded-lg border ${oc}"><span class="text-[10px] font-bold uppercase">${o.kind}: ${o.status}</span>`;
        if (o.details && typeof o.details === 'object') html += `<pre class="text-[10px] text-slate-300 ml-auto mono whitespace-pre-wrap">${JSON.stringify(o.details,null,2)}</pre>`;
        html += '</div>';
      });
      html += '</div>';
    }
    // LLM Calls
    if (d.calls && d.calls.length) {
      html += `<div class="space-y-2"><h4 class="text-[10px] font-bold text-cyan-400 uppercase tracking-wider px-1">LLM Calls (${d.calls.length})</h4>`;
      d.calls.forEach((c, i) => {
        const latColor = (c.latency_ms||0) > 5000 ? 'text-amber-400' : 'text-slate-300';
        html += `<details class="card group"><summary class="p-3 cursor-pointer flex items-center justify-between hover:bg-surface-800/40 rounded-2xl transition">
          <div class="flex items-center gap-2">
            <span class="h-5 w-5 rounded bg-surface-800 flex items-center justify-center text-[10px] font-bold text-slate-400 border border-surface-700">${i+1}</span>
            <span class="mono text-xs font-semibold text-slate-200">${c.model||'—'}</span>
            <span class="text-[10px] ${c.status_code===200?'text-emerald-400':'text-rose-400'} font-bold">${c.status_code||'—'}</span>
          </div>
          <div class="flex items-center gap-3 text-[10px]">
            <span class="${latColor} font-semibold">${c.latency_ms?c.latency_ms+'ms':'—'}</span>
            <span class="text-slate-500">${(c.input_tokens||0)}→${(c.output_tokens||0)} tok</span>
          </div>
        </summary>
        <div class="px-3 pb-3 space-y-2 border-t border-surface-700 mt-1 pt-2 text-[11px]">
          <div><span class="text-slate-500 text-[10px] font-bold uppercase">Upstream:</span> <span class="mono text-slate-400">${c.upstream||'—'}</span></div>
          <div><span class="text-slate-500 text-[10px] font-bold uppercase">Style:</span> <span class="text-slate-400">${c.api_style||'—'}</span></div>
          ${c.error?'<div class="p-2 rounded-lg bg-rose-950/30 border border-rose-800/30 text-rose-300 mono text-[10px]">'+c.error+'</div>':''}
        </div></details>`;
      });
      html += '</div>';
    }
    content.innerHTML = html;
  } catch(e) { content.innerHTML = '<p class="text-xs text-rose-400">Error: '+e+'</p>'; }
}
function closeTracePanel() { document.getElementById('trace-panel').classList.add('hidden'); }

// ────────── Graph Modes & Controls ──────────
function switchGraphMode(mode) {
  currentGraphMode = mode;
  const bAct = document.getElementById('graph-tab-activity');
  const bTok = document.getElementById('graph-tab-tokens');
  const bSpl = document.getElementById('graph-tab-split');
  if (bAct) bAct.className = mode === 'activity' ? 'px-2.5 py-1 rounded-md font-bold text-white bg-indigo-600 transition' : 'px-2.5 py-1 rounded-md font-semibold text-slate-400 hover:text-white transition';
  if (bTok) bTok.className = mode === 'tokens' ? 'px-2.5 py-1 rounded-md font-bold text-white bg-cyan-600 transition' : 'px-2.5 py-1 rounded-md font-semibold text-slate-400 hover:text-white transition';
  if (bSpl) bSpl.className = mode === 'split' ? 'px-2.5 py-1 rounded-md font-bold text-white bg-violet-600 transition' : 'px-2.5 py-1 rounded-md font-semibold text-slate-400 hover:text-white transition hidden md:inline';

  const wAct = document.getElementById('wrapper-activity');
  const wTok = document.getElementById('wrapper-tokens');
  const grid = document.getElementById('charts-grid');
  const sum = document.getElementById('chart-summary-text');

  if (mode === 'activity') {
    if (grid) grid.className = 'grid grid-cols-1 gap-2';
    if (wAct) wAct.classList.remove('hidden');
    if (wTok) wTok.classList.add('hidden');
    if (sum) sum.textContent = 'Daily calls volume';
  } else if (mode === 'tokens') {
    if (grid) grid.className = 'grid grid-cols-1 gap-2';
    if (wAct) wAct.classList.add('hidden');
    if (wTok) wTok.classList.remove('hidden');
    if (sum) sum.textContent = 'Token breakdown (In/Out)';
  } else {
    if (grid) grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-3';
    if (wAct) wAct.classList.remove('hidden');
    if (wTok) wTok.classList.remove('hidden');
    if (sum) sum.textContent = 'Dual telemetry view';
  }
  if (activityChart) setTimeout(() => activityChart.resize(), 50);
  if (tokenChart) setTimeout(() => tokenChart.resize(), 50);
}

function setChartRange(days) {
  currentChartDays = days;
  [7, 14, 30].forEach(d => {
    const el = document.getElementById('range-' + d);
    if (el) el.className = d === days ? 'px-2 py-0.5 rounded text-indigo-300 bg-surface-800 transition font-bold' : 'px-2 py-0.5 rounded text-slate-400 hover:text-white transition';
  });
  fetchTimeseries();
}

function toggleChartCollapse() {
  chartCollapsed = !chartCollapsed;
  const body = document.getElementById('chart-container-body');
  const icon = document.getElementById('chart-collapse-icon');
  const label = document.getElementById('chart-collapse-label');
  if (chartCollapsed) {
    body.classList.add('hidden');
    icon.textContent = '▸';
    if (label) label.textContent = 'Open';
  } else {
    body.classList.remove('hidden');
    icon.textContent = '▾';
    if (label) label.textContent = 'Fold';
    if (activityChart) setTimeout(() => activityChart.resize(), 50);
    if (tokenChart) setTimeout(() => tokenChart.resize(), 50);
  }
}

// ────────── Charts ──────────
function renderCharts(series, days) {
  const labels = []; const dailyCalls = {}; const dailyIn = {}; const dailyOut = {};
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const key = d.toISOString().split('T')[0]; labels.push(d.toLocaleDateString('en', {month:'short',day:'numeric'}));
    dailyCalls[key] = 0; dailyIn[key] = 0; dailyOut[key] = 0;
  }
  series.forEach(s => { const k = s.day; if (k in dailyCalls) { dailyCalls[k] += s.calls||0; dailyIn[k] += s.input_tokens||0; dailyOut[k] += s.output_tokens||0; } });

  const callData = labels.map((_,i) => dailyCalls[Object.keys(dailyCalls)[i]]||0);
  const inData = labels.map((_,i) => dailyIn[Object.keys(dailyIn)[i]]||0);
  const outData = labels.map((_,i) => dailyOut[Object.keys(dailyOut)[i]]||0);

  const chartOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        align: 'end',
        labels: { color: '#94a3b8', font: { size: 10, family: 'Inter' }, boxWidth: 8, boxHeight: 8, usePointStyle: true, pointStyle: 'circle' }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 20, 36, 0.95)',
        borderColor: '#1e2740',
        borderWidth: 1,
        titleFont: { size: 10, family: 'Inter', weight: 'bold' },
        bodyFont: { size: 10, family: 'Inter' },
        padding: 6,
        cornerRadius: 6
      }
    },
    scales: {
      x: {
        ticks: { color: '#64748b', font: { size: 9 } },
        grid: { display: false }
      },
      y: {
        beginAtZero: true,
        ticks: { color: '#64748b', font: { size: 9 }, precision: 0 },
        grid: { color: 'rgba(255,255,255,0.03)' }
      }
    }
  };

  if (activityChart) activityChart.destroy();
  const ctx1 = document.getElementById('chart-activity').getContext('2d');
  activityChart = new Chart(ctx1, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Calls',
        data: callData,
        borderColor: '#818cf8',
        backgroundColor: 'rgba(129,140,248,0.08)',
        fill: true,
        tension: 0.3,
        pointRadius: 2.5,
        pointHoverRadius: 5,
        pointBackgroundColor: '#818cf8',
        borderWidth: 2
      }]
    },
    options: chartOpts
  });

  if (tokenChart) tokenChart.destroy();
  const ctx2 = document.getElementById('chart-tokens').getContext('2d');
  tokenChart = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Input', data: inData, backgroundColor: 'rgba(6,182,212,0.6)', borderColor: '#06b6d4', borderWidth: 1, borderRadius: 3, maxBarThickness: 24 },
        { label: 'Output', data: outData, backgroundColor: 'rgba(16,185,129,0.6)', borderColor: '#10b981', borderWidth: 1, borderRadius: 3, maxBarThickness: 24 }
      ]
    },
    options: {
      ...chartOpts,
      scales: {
        ...chartOpts.scales,
        x: { ...chartOpts.scales.x, stacked: true },
        y: { ...chartOpts.scales.y, stacked: true }
      }
    }
  });
}

// ────────── IDE Setup Cards ──────────
function renderIDECards() {
  const server = location.origin;
  const cards = [
    { icon: '🤖', name: 'Cursor / VS Code (Continue)', desc: 'Route directly to ObserverCoder-1.0 multi-model assistant.', code: `Base URL: ${server}/v1\\nModel: observer-coder-1.0\\nAPI Key: <your-personal-key>` },
    { icon: '🐚', name: 'PowerShell', desc: 'Paste into your terminal to route all OpenAI SDK calls through Observer.', code: `$env:OPENAI_BASE_URL="${server}/v1"\\n$env:OPENAI_API_KEY="<your-key>"\\n$env:X_SESSION_ID="${S.user}"` },
    { icon: '🐧', name: 'Bash / Zsh', desc: 'Export environment variables in your shell session.', code: `export OPENAI_BASE_URL="${server}/v1"\\nexport OPENAI_API_KEY="<your-key>"\\nexport X_SESSION_ID="${S.user}"` },
    { icon: '📦', name: 'pip Install (Global CLI)', desc: 'Install the observer CLI package and run activate.', code: `pip install git+https://github.com/baizo7/observer.git\\nobserver activate` },
  ];
  const container = document.getElementById('ide-cards');
  container.innerHTML = '';
  cards.forEach(c => {
    const div = document.createElement('div');
    div.className = 'card p-4 space-y-3 hover:border-indigo-800/40 transition';
    div.innerHTML = `<div class="flex items-center gap-2"><span class="text-xl">${c.icon}</span><h4 class="text-xs font-bold text-white">${c.name}</h4></div>
    <p class="text-[11px] text-slate-400">${c.desc}</p>
    <pre class="bg-surface-950 border border-surface-700 rounded-lg p-3 text-[11px] mono text-cyan-300 whitespace-pre-wrap overflow-x-auto">${c.code}</pre>
    <button class="copy-btn px-3 py-1.5 bg-surface-800 hover:bg-surface-700 text-indigo-300 rounded-lg text-[11px] font-bold border border-surface-700 transition w-full">📋 Copy to Clipboard</button>`;
    const btn = div.querySelector('button');
    btn.onclick = () => copyText(btn, c.code);
    container.appendChild(div);
  });
}
function copyText(btn, text) {
  navigator.clipboard.writeText(text);
  btn.textContent = '✓ Copied!'; btn.classList.add('text-emerald-400');
  setTimeout(() => { btn.textContent = '📋 Copy to Clipboard'; btn.classList.remove('text-emerald-400'); }, 2000);
}

// ────────── Model Compare ──────────
function renderCompare() {
  const grid = document.getElementById('compare-grid');
  const stats = S.statsCache || [];
  if (!stats.length) { grid.innerHTML = '<p class="text-xs text-slate-500 col-span-3">No model data available yet.</p>'; return; }
  grid.innerHTML = '';
  const sorted = [...stats].sort((a,b) => (b.calls||0) - (a.calls||0));
  sorted.forEach(m => {
    const ot = (m.passes||0)+(m.fails||0); const rate = ot > 0 ? Math.round((m.passes/ot)*100) : null;
    const cost = estimateCost(m.model, m.input_tokens, m.output_tokens);
    const efficiency = (m.calls||0) > 0 ? Math.round(((m.output_tokens||0) / (m.calls||0))) : 0;
    const rc = rate >= 70 ? 'text-emerald-400' : rate >= 40 ? 'text-amber-400' : 'text-slate-500';
    const ringPct = rate !== null ? rate : 0;
    const div = document.createElement('div');
    div.className = 'card p-4 space-y-3 hover:border-indigo-800/40 transition';
    div.innerHTML = `<div class="flex items-center justify-between"><h4 class="mono text-xs font-bold text-white truncate">${m.model}</h4><span class="text-xl font-black ${rc}">${rate!==null?rate+'%':'—'}</span></div>
    <div class="w-full bg-surface-800 rounded-full h-1.5"><div class="h-1.5 rounded-full ${rate>=70?'bg-emerald-500':rate>=40?'bg-amber-500':'bg-slate-600'}" style="width:${ringPct}%"></div></div>
    <div class="grid grid-cols-2 gap-2 text-[11px]">
      <div><span class="text-slate-500">Calls</span><p class="font-bold text-white">${(m.calls||0).toLocaleString()}</p></div>
      <div><span class="text-slate-500">Avg Latency</span><p class="font-bold text-cyan-400">${m.avg_latency_ms?m.avg_latency_ms+'ms':'—'}</p></div>
      <div><span class="text-slate-500">Output/Call</span><p class="font-bold text-slate-200">${efficiency} tok</p></div>
      <div><span class="text-slate-500">Est. Cost</span><p class="font-bold text-amber-400">${fmtCost(cost)}</p></div>
      <div><span class="text-slate-500">Pass</span><p class="font-bold text-emerald-400">${m.passes||0}</p></div>
      <div><span class="text-slate-500">Fail</span><p class="font-bold text-rose-400">${m.fails||0}</p></div>
    </div>`;
    grid.appendChild(div);
  });
  // Recommendation
  const best = sorted.reduce((a,b) => { const ra = ((a.passes||0)/((a.passes||0)+(a.fails||0)||1))*100; const rb = ((b.passes||0)/((b.passes||0)+(b.fails||0)||1))*100; return ra >= rb && (a.calls||0)>=3 ? a : b; }, sorted[0]);
  const fastest = sorted.reduce((a,b) => (a.avg_latency_ms||9999) < (b.avg_latency_ms||9999) ? a : b, sorted[0]);
  const cheapest = sorted.reduce((a,b) => estimateCost(a.model,a.input_tokens,a.output_tokens)/(a.calls||1) < estimateCost(b.model,b.input_tokens,b.output_tokens)/(b.calls||1) ? a : b, sorted[0]);
  document.getElementById('compare-recommendation').innerHTML = `<div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
    <div><span class="text-emerald-400 font-bold">Best Pass Rate:</span> <span class="mono text-white font-semibold">${best.model}</span></div>
    <div><span class="text-cyan-400 font-bold">Lowest Latency:</span> <span class="mono text-white font-semibold">${fastest.model}</span> (${fastest.avg_latency_ms}ms)</div>
    <div><span class="text-amber-400 font-bold">Most Cost-Efficient:</span> <span class="mono text-white font-semibold">${cheapest.model}</span></div>
  </div>`;
}

// ────────── Dataset Export ──────────
function setExportType(t) {
  S.exportType = t;
  document.getElementById('btn-sft').className = t==='sft' ? 'flex-1 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white border border-indigo-500 transition' : 'flex-1 py-2 rounded-lg text-xs font-bold bg-surface-800 text-slate-400 border border-surface-700 transition';
  document.getElementById('btn-dpo').className = t==='dpo' ? 'flex-1 py-2 rounded-lg text-xs font-bold bg-violet-600 text-white border border-violet-500 transition' : 'flex-1 py-2 rounded-lg text-xs font-bold bg-surface-800 text-slate-400 border border-surface-700 transition';
  document.getElementById('export-type-desc').textContent = t==='sft' ? 'Supervised Fine-Tuning — ShareGPT format with verified prompt→response pairs.' : 'Direct Preference Optimization — chosen vs rejected pairs for RLHF training.';
}
async function runExport() {
  const btn = document.getElementById('export-run-btn');
  const status = document.getElementById('export-status');
  btn.disabled = true; btn.textContent = 'Generating...'; status.textContent = '';
  const payload = { dataset_type: S.exportType, project: document.getElementById('export-project').value || null, limit: parseInt(document.getElementById('export-limit').value) || 500, deduplicate: true, val_split: 0.2 };
  try {
    const r = await fetch('/admin/export-dataset', { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify(payload) });
    if (!r.ok) { const e = await r.json(); status.textContent = 'Error: ' + (e.error||r.statusText); btn.disabled = false; btn.textContent = 'Generate & Download .jsonl'; return; }
    const d = await r.json();
    // Show summary
    const preview = document.getElementById('export-preview'); preview.classList.remove('hidden');
    const sumEl = document.getElementById('export-summary-content');
    const s = d.summary || {};
    sumEl.innerHTML = `<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div><span class="text-slate-500">Type</span><p class="font-bold text-white">${d.dataset_type.toUpperCase()}</p></div>
      <div><span class="text-slate-500">Train</span><p class="font-bold text-emerald-400">${d.splits?.train_count||0} samples</p></div>
      <div><span class="text-slate-500">Validation</span><p class="font-bold text-cyan-400">${d.splits?.validation_count||0} samples</p></div>
      <div><span class="text-slate-500">Total Tokens</span><p class="font-bold text-white">${(s.total_tokens||0).toLocaleString()}</p></div>
    </div>`;
    // Download as .jsonl
    const allRecords = [...(d.train||[]), ...(d.validation||[])];
    const jsonl = allRecords.map(r => JSON.stringify(r)).join('\\n');
    const blob = new Blob([jsonl], {type:'application/jsonl'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `observer_${d.dataset_type}_dataset.jsonl`; a.click();
    URL.revokeObjectURL(url);
    status.textContent = '✓ Downloaded ' + allRecords.length + ' records.';
  } catch(e) { status.textContent = 'Error: ' + e; }
  btn.disabled = false; btn.textContent = 'Generate & Download .jsonl';
}

// ────────── Modal ──────────
function openAccessModal() { document.getElementById('access-modal').classList.remove('hidden'); document.getElementById('access-modal').classList.add('flex'); }
function closeAccessModal() { document.getElementById('access-modal').classList.add('hidden'); document.getElementById('access-modal').classList.remove('flex'); }
function switchModalTab(t) {
  document.getElementById('tab-btn-dev').className = t==='dev' ? "py-2 rounded-md bg-indigo-600 text-white transition" : "py-2 rounded-md text-slate-400 hover:text-white transition";
  document.getElementById('tab-btn-admin').className = t==='admin' ? "py-2 rounded-md bg-violet-600 text-white transition" : "py-2 rounded-md text-slate-400 hover:text-white transition";
  document.getElementById('modal-tab-dev').classList.toggle('hidden', t!=='dev');
  document.getElementById('modal-tab-admin').classList.toggle('hidden', t!=='admin');
}
function submitDeveloperLogin() {
  S.user = document.getElementById('modal-input-user').value.trim() || 'dev';
  S.role = 'dev'; S.adminToken = ''; S.filterUser = null;
  localStorage.setItem('ao_user', S.user); localStorage.removeItem('ao_admin_token');
  closeAccessModal(); updateUIForRole(); fetchData(); initWebSocket(); fetchQuotas();
}
async function submitAdminLogin() {
  const key = document.getElementById('modal-input-admin-key').value.trim(); if (!key) return;
  try {
    const r = await fetch('/admin/verify', { headers: { 'X-Admin-Token': key, 'Authorization': 'Bearer '+key } });
    if (r.ok) { S.role='admin'; S.adminToken=key; S.filterUser=null; localStorage.setItem('ao_admin_token',key); closeAccessModal(); updateUIForRole(); fetchData(); initWebSocket(); fetchQuotas(); }
    else alert('Invalid Admin Key.');
  } catch(e) { alert('Error: '+e); }
}

// ────────── Phase 6: WebSockets Live Stream ──────────
function initWebSocket() {
  if (S.ws) {
    try { S.ws.close(); } catch(e) {}
    S.ws = null;
  }
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  let wsUrl = `${proto}//${location.host}/ws/live`;
  const params = [];
  if (S.adminToken) params.push('admin_token=' + encodeURIComponent(S.adminToken));
  if (S.user) params.push('session_id=' + encodeURIComponent(S.user));
  if (params.length) wsUrl += '?' + params.join('&');

  const liveBadge = document.getElementById('live-badge');
  const liveDot = document.getElementById('live-dot');
  const liveText = document.getElementById('live-text');

  try {
    const ws = new WebSocket(wsUrl);
    S.ws = ws;

    ws.onopen = () => {
      if (liveBadge) liveBadge.className = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/50";
      if (liveDot) liveDot.className = "h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse";
      if (liveText) liveText.textContent = "⚡ Live Feed";
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'call') {
          handleLiveCall(msg.data);
        } else if (msg.type === 'outcome') {
          handleLiveOutcome(msg.data);
        } else if (msg.type === 'retrain_completed') {
          handleLiveRetrainCompleted(msg.data);
        }
      } catch (err) {
        console.debug("WS parse error", err);
      }
    };

    ws.onclose = () => {
      if (liveBadge) liveBadge.className = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-surface-800 text-slate-400 border border-surface-700";
      if (liveDot) liveDot.className = "h-1.5 w-1.5 rounded-full bg-slate-500";
      if (liveText) liveText.textContent = "Live WS (reconnecting)";
      setTimeout(() => {
        if (!S.ws || S.ws.readyState === WebSocket.CLOSED) {
          initWebSocket();
        }
      }, 5000);
    };

    ws.onerror = () => {
      try { ws.close(); } catch(e) {}
    };
  } catch (err) {
    console.debug("WS init error", err);
  }
}

function handleLiveCall(c) {
  const totCallsEl = document.getElementById('total-calls');
  if (totCallsEl && totCallsEl.textContent !== '—') {
    const current = parseInt(totCallsEl.textContent.replace(/,/g, '')) || 0;
    totCallsEl.textContent = (current + 1).toLocaleString();
  }
  const tb = document.getElementById('tasks-body');
  if (tb && c.task_id) {
    let existingRow = document.getElementById('task-row-' + c.task_id);
    if (!existingRow) {
      const tr = document.createElement('tr');
      tr.id = 'task-row-' + c.task_id;
      tr.className = "hover:bg-surface-800/60 cursor-pointer transition border-b border-surface-700/50 bg-indigo-950/40 fade-in";
      tr.onclick = () => openTracePanel(c.task_id);
      tr.innerHTML = `
        <td class="py-2.5 px-4 font-mono text-cyan-400 font-semibold flex items-center gap-2">
          <span class="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse"></span>${c.task_id}
        </td>
        <td class="py-2.5 px-4 text-slate-300">${c.project||'—'}</td>
        <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-surface-800 text-slate-300">coding</span></td>
        <td class="py-2.5 px-4 text-white font-bold" id="task-calls-${c.task_id}">1</td>
        <td class="py-2.5 px-4 font-mono text-slate-300 text-xs">${c.model||'—'}</td>
        <td class="py-2.5 px-4" id="task-outcome-${c.task_id}"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-surface-800 text-slate-400">running</span></td>
        <td class="py-2.5 px-4 text-slate-500 text-[11px]">Just now</td>
      `;
      if (tb.firstChild) tb.insertBefore(tr, tb.firstChild);
      else tb.appendChild(tr);
    } else {
      const callsCell = document.getElementById('task-calls-' + c.task_id);
      if (callsCell) {
        const count = parseInt(callsCell.textContent) || 0;
        callsCell.textContent = count + 1;
      }
      existingRow.classList.add('bg-indigo-950/40');
      setTimeout(() => existingRow.classList.remove('bg-indigo-950/40'), 1500);
    }
  }
}

function handleLiveOutcome(o) {
  const badge = document.getElementById('task-outcome-' + o.task_id);
  if (badge) {
    if (o.status === 'pass' || o.status === 'accepted') {
      badge.innerHTML = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">pass</span>';
    } else {
      badge.innerHTML = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800">fail</span>';
    }
  }
}

function handleLiveRetrainCompleted(data) {
  const statusEl = document.getElementById('retrain-status-text');
  if (statusEl) {
    statusEl.innerHTML = `<span class="text-emerald-400 font-bold">✓ Job ${data.job_id} Completed! Adapter saved at ${data.adapter_path}</span>`;
  }
}

// ────────── Phase 6: Quotas & Loop Alerts ──────────
async function fetchQuotas() {
  try {
    let qUrl = '/stats/quotas';
    if (S.role !== 'admin' && S.user) {
      qUrl += '?session_id=' + encodeURIComponent(S.user);
    } else if (S.role === 'admin' && S.filterUser) {
      qUrl += '?session_id=' + encodeURIComponent(S.filterUser);
    }
    const res = await fetch(qUrl, { headers: authHeaders() });
    if (!res.ok) return;
    const d = await res.json();

    const qText = document.getElementById('banner-quota-text');
    const qBar = document.getElementById('banner-quota-bar');
    if (qText && qBar) {
      const pct = Math.min(100, d.usage_pct || 0);
      qText.textContent = `${(d.tokens_today||0).toLocaleString()} / ${(d.daily_budget||100000).toLocaleString()} (${pct}%)`;
      qBar.style.width = pct + '%';
      if (pct >= 90) {
        qBar.className = "h-full bg-rose-500 transition-all duration-300";
        qText.className = "text-[10px] font-bold text-rose-400 ml-0.5";
      } else if (pct >= 70) {
        qBar.className = "h-full bg-amber-400 transition-all duration-300";
        qText.className = "text-[10px] font-bold text-amber-400 ml-0.5";
      } else {
        qBar.className = "h-full bg-cyan-400 transition-all duration-300";
        qText.className = "text-[10px] font-bold text-cyan-400 ml-0.5";
      }
    }

    const loopBanner = document.getElementById('loop-alert-banner');
    if (d.loop_detected && d.active_alerts && d.active_alerts.length > 0) {
      const topAlert = d.active_alerts[0];
      S.stuckTaskId = topAlert.task_id;
      document.getElementById('loop-alert-msg').textContent = topAlert.reason;
      document.getElementById('loop-alert-badge').textContent = (topAlert.severity || 'WARNING').toUpperCase();
      loopBanner.classList.remove('hidden');
    } else {
      loopBanner.classList.add('hidden');
    }
  } catch(e) {
    console.debug('Quota fetch error', e);
  }
}

function inspectStuckTask() {
  if (S.stuckTaskId) {
    openTracePanel(S.stuckTaskId);
  }
}

// ────────── Phase 6: Retraining Center ──────────
async function triggerRetraining() {
  const btn = document.getElementById('retrain-run-btn');
  const spinner = document.getElementById('retrain-spinner');
  const statusText = document.getElementById('retrain-status-text');
  const consoleEl = document.getElementById('retrain-console');
  const logEl = document.getElementById('retrain-log-output');
  const progressBar = document.getElementById('retrain-progress-bar');
  const jobIdEl = document.getElementById('retrain-job-id');

  const model = document.getElementById('retrain-model').value;
  const datasetType = document.getElementById('retrain-dataset-type').value;
  const rank = parseInt(document.getElementById('retrain-rank').value) || 16;
  const epochs = parseInt(document.getElementById('retrain-epochs').value) || 3;

  btn.disabled = true;
  spinner.classList.remove('hidden');
  statusText.textContent = 'Queueing job...';
  consoleEl.classList.remove('hidden');
  logEl.innerHTML = '';
  progressBar.style.width = '10%';

  try {
    const res = await fetch('/admin/retrain/trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ model, dataset_type: datasetType, rank, alpha: rank * 2, epochs }),
    });

    if (!res.ok) {
      const err = await res.json();
      statusText.textContent = 'Error: ' + (err.error || res.statusText);
      btn.disabled = false;
      spinner.classList.add('hidden');
      return;
    }

    const data = await res.json();
    jobIdEl.textContent = data.job_id;
    statusText.textContent = 'Job running in background...';

    pollRetrainingJob(data.job_id);
  } catch(e) {
    statusText.textContent = 'Error: ' + e;
    btn.disabled = false;
    spinner.classList.add('hidden');
  }
}

function pollRetrainingJob(jobId) {
  if (S.retrainPollTimer) clearInterval(S.retrainPollTimer);

  S.retrainPollTimer = setInterval(async () => {
    try {
      const res = await fetch('/admin/retrain/status/' + encodeURIComponent(jobId), {
        headers: authHeaders(),
      });
      if (!res.ok) return;
      const job = await res.json();

      const logEl = document.getElementById('retrain-log-output');
      const progressBar = document.getElementById('retrain-progress-bar');
      const statusText = document.getElementById('retrain-status-text');
      const btn = document.getElementById('retrain-run-btn');
      const spinner = document.getElementById('retrain-spinner');

      progressBar.style.width = (job.progress || 10) + '%';
      logEl.innerHTML = (job.logs || []).map(l => `<div class="text-slate-300">${l}</div>`).join('');
      logEl.scrollTop = logEl.scrollHeight;

      if (job.status === 'completed') {
        clearInterval(S.retrainPollTimer);
        S.retrainPollTimer = null;
        btn.disabled = false;
        spinner.classList.add('hidden');
        statusText.innerHTML = `<span class="text-emerald-400 font-bold">✓ Retraining complete! Adapter saved to ${job.adapter_path}</span>`;
      } else if (job.status === 'failed') {
        clearInterval(S.retrainPollTimer);
        S.retrainPollTimer = null;
        btn.disabled = false;
        spinner.classList.add('hidden');
        statusText.innerHTML = `<span class="text-rose-400 font-bold">✕ Retraining failed: ${job.error || 'Unknown error'}</span>`;
      }
    } catch(e) {
      console.debug('Retrain poll error', e);
    }
  }, 1000);
}

// ────────── Boot ──────────
initAuth(); fetchData(); initWebSocket(); fetchQuotas(); setInterval(fetchData, 8000); setInterval(fetchQuotas, 10000);
</script>
</body>
</html>
"""
