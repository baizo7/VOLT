"""
Interactive analytics and role-based access control dashboard for AI Model Observer.
Admin Mode: Full visibility into connected developers, masked API keys, team-wide model performance, and datasets.
Developer Mode: Scoped view showing only personal API usage, configured models, and active tasks.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-950 text-slate-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Model Observer - Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap">
  <style>
    body { font-family: 'Inter', sans-serif; }
    code, pre { font-family: 'JetBrains Mono', monospace; }
    [x-cloak] { display: none !important; }
  </style>
</head>
<body class="min-h-full flex flex-col p-4 md:p-6 max-w-7xl mx-auto space-y-6">

  <!-- Top Navigation & Access Control Bar -->
  <header class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
    <div class="flex items-center space-x-3">
      <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/25">
        AO
      </div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-xl font-bold tracking-tight text-white">AI Model Observer</h1>
          <span id="role-badge" class="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            Checking Access...
          </span>
        </div>
        <p class="text-xs text-slate-400">Capture Proxy &bull; Telemetry &bull; Role-Based Access Control</p>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <span id="health-badge" class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
        <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
        Connecting...
      </span>
      <button onclick="fetchData()" class="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition">
        Refresh
      </button>
      <button onclick="openAccessModal()" class="px-3 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-sm transition">
        Switch View / Login
      </button>
    </div>
  </header>

  <!-- User Scope Banner (Visible in Developer Mode) -->
  <section id="developer-banner" class="hidden bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-indigo-900/50 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
    <div class="flex items-center gap-3">
      <div class="h-9 w-9 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-sm border border-indigo-500/30">
        👤
      </div>
      <div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-indigo-400">Developer Profile:</span>
          <span id="banner-user-name" class="font-bold text-white text-sm">dev</span>
        </div>
        <p class="text-xs text-slate-400">Showing only personal requests, configured models, and active tasks.</p>
      </div>
    </div>
    <div class="flex items-center gap-4 text-xs">
      <div class="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
        <span class="text-slate-400">Configured Key:</span>
        <span id="banner-masked-key" class="font-mono text-cyan-400 font-semibold ml-1">not-configured</span>
      </div>
      <div class="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
        <span class="text-slate-400">Provider:</span>
        <span id="banner-provider" class="uppercase font-semibold text-slate-200 ml-1">GEMINI</span>
      </div>
    </div>
  </section>

  <!-- Metrics Grid -->
  <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Calls</span>
      <p id="total-calls" class="text-2xl font-bold text-white mt-1">-</p>
      <span id="total-calls-sub" class="text-[11px] text-slate-500">Proxied LLM traces</span>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Avg Latency</span>
      <p id="avg-latency" class="text-2xl font-bold text-indigo-400 mt-1">-</p>
      <span class="text-[11px] text-slate-500">Milliseconds / call</span>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Tokens</span>
      <p id="total-tokens" class="text-2xl font-bold text-cyan-400 mt-1">-</p>
      <span id="token-split" class="text-[11px] text-slate-500">In: - | Out: -</span>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Overall Pass Rate</span>
      <p id="pass-rate" class="text-2xl font-bold text-emerald-400 mt-1">-</p>
      <span id="pass-counts" class="text-[11px] text-slate-500">- passes / - fails</span>
    </div>
  </section>

  <!-- ADMIN ONLY: Connected Developers & Configured API Keys -->
  <section id="admin-developers-section" class="hidden bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
    <div class="p-4 border-b border-slate-800 flex flex-wrap justify-between items-center gap-2 bg-slate-950/40">
      <div>
        <h2 class="text-sm font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
          <span>👑</span> Connected Developers & Configured API Keys
        </h2>
        <p class="text-xs text-slate-400">All developers who connected their personal API keys to this central Observer instance</p>
      </div>
      <span id="connected-count" class="text-xs px-2.5 py-1 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-semibold">
        0 Active Developers
      </span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-slate-300">
        <thead class="bg-slate-950/60 text-xs text-slate-400 border-b border-slate-800 uppercase">
          <tr>
            <th class="py-3 px-4">Developer</th>
            <th class="py-3 px-4">Project</th>
            <th class="py-3 px-4">Configured Key</th>
            <th class="py-3 px-4">Provider</th>
            <th class="py-3 px-4">Models Used</th>
            <th class="py-3 px-4">Total Calls</th>
            <th class="py-3 px-4">Total Tokens</th>
            <th class="py-3 px-4">Last Active</th>
            <th class="py-3 px-4">Action</th>
          </tr>
        </thead>
        <tbody id="developers-body" class="divide-y divide-slate-800">
          <tr><td colspan="9" class="py-6 text-center text-slate-500">Loading connected developers...</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- Model Performance Leaderboard -->
  <section class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
    <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/40">
      <div>
        <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wider">Model Performance Leaderboard</h2>
        <p id="leaderboard-sub" class="text-xs text-slate-400">Aggregated execution performance and last-touch attribution</p>
      </div>
      <span id="active-filter-indicator" class="text-xs text-indigo-400 font-medium"></span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-slate-300">
        <thead class="bg-slate-950/60 text-xs text-slate-400 border-b border-slate-800 uppercase">
          <tr>
            <th class="py-3 px-4">Model</th>
            <th class="py-3 px-4">Calls</th>
            <th class="py-3 px-4">Avg Latency</th>
            <th class="py-3 px-4">Input Tokens</th>
            <th class="py-3 px-4">Output Tokens</th>
            <th class="py-3 px-4">Pass / Fail</th>
            <th class="py-3 px-4">Success Rate</th>
          </tr>
        </thead>
        <tbody id="models-body" class="divide-y divide-slate-800">
          <tr><td colspan="7" class="py-6 text-center text-slate-500">Loading model performance...</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- Recent Tasks & Outcomes -->
  <section class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
    <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/40">
      <div>
        <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wider">Recent Tasks & Outcomes</h2>
        <p id="tasks-sub" class="text-xs text-slate-400">Latest active development sessions</p>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-slate-300">
        <thead class="bg-slate-950/60 text-xs text-slate-400 border-b border-slate-800 uppercase">
          <tr>
            <th class="py-3 px-4">Task ID</th>
            <th class="py-3 px-4">Project</th>
            <th class="py-3 px-4">Task Type</th>
            <th class="py-3 px-4">Calls</th>
            <th class="py-3 px-4">Primary Model</th>
            <th class="py-3 px-4">Outcome</th>
            <th class="py-3 px-4">Created</th>
          </tr>
        </thead>
        <tbody id="tasks-body" class="divide-y divide-slate-800">
          <tr><td colspan="7" class="py-6 text-center text-slate-500">Loading tasks...</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- Footer -->
  <footer class="pt-4 border-t border-slate-800/80 text-xs text-slate-500 flex justify-between items-center">
    <span>AI Model Observer &bull; Role-Based Access Control</span>
    <span>Auto-refreshes every 5s</span>
  </footer>

  <!-- Access Control Modal (Login / Switch Role) -->
  <div id="access-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm hidden items-center justify-center p-4 z-50">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="font-bold text-white text-base">Select Dashboard View</h3>
        <button onclick="closeAccessModal()" class="text-slate-400 hover:text-white">&times;</button>
      </div>

      <!-- Tab Buttons -->
      <div class="grid grid-cols-2 gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-semibold">
        <button id="tab-btn-dev" onclick="switchModalTab('dev')" class="py-2 rounded-md bg-indigo-600 text-white transition">
          👤 Developer View
        </button>
        <button id="tab-btn-admin" onclick="switchModalTab('admin')" class="py-2 rounded-md text-slate-400 hover:text-white transition">
          👑 Admin View
        </button>
      </div>

      <!-- Developer Form -->
      <div id="modal-tab-dev" class="space-y-4">
        <p class="text-xs text-slate-400">View only your personal usage, configured API key, and tasks.</p>
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1">Developer Name / Session ID</label>
          <input id="modal-input-user" type="text" placeholder="e.g. alex" class="w-full px-3 py-2 text-sm bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500">
        </div>
        <button onclick="submitDeveloperLogin()" class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white rounded-lg transition shadow-md">
          Enter Personal Dashboard
        </button>
      </div>

      <!-- Admin Form -->
      <div id="modal-tab-admin" class="space-y-4 hidden">
        <p class="text-xs text-slate-400">Access full system visibility, connected developer keys, and export tools.</p>
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1">Admin Secret Key / Token</label>
          <input id="modal-input-admin-key" type="password" placeholder="Enter OBSERVER_ADMIN_KEY" class="w-full px-3 py-2 text-sm bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500">
        </div>
        <button onclick="submitAdminLogin()" class="w-full py-2.5 bg-violet-600 hover:bg-violet-500 font-semibold text-xs text-white rounded-lg transition shadow-md">
          Unlock Admin Dashboard
        </button>
      </div>
    </div>
  </div>

  <script>
    // State management
    const urlParams = new URLSearchParams(window.location.search);
    let state = {
      role: 'guest', // 'admin' | 'dev'
      user: urlParams.get('user') || localStorage.getItem('ao_user') || '',
      adminToken: urlParams.get('admin_token') || urlParams.get('token') || localStorage.getItem('ao_admin_token') || '',
      filterUser: null,
    };

    function initAuth() {
      if (state.adminToken) {
        state.role = 'admin';
      } else if (state.user) {
        state.role = 'dev';
      } else {
        state.role = 'dev';
        state.user = 'dev';
      }
      updateUIForRole();
    }

    function updateUIForRole() {
      const roleBadge = document.getElementById('role-badge');
      const devBanner = document.getElementById('developer-banner');
      const adminSection = document.getElementById('admin-developers-section');
      const totalCallsSub = document.getElementById('total-calls-sub');
      const leaderboardSub = document.getElementById('leaderboard-sub');
      const tasksSub = document.getElementById('tasks-sub');

      if (state.role === 'admin') {
        roleBadge.className = "px-2.5 py-0.5 text-[11px] font-bold rounded-full bg-violet-950 text-violet-300 border border-violet-800 shadow-sm";
        roleBadge.innerHTML = "👑 Admin View";
        devBanner.classList.add('hidden');
        adminSection.classList.remove('hidden');
        totalCallsSub.innerText = "All team traces";
        leaderboardSub.innerText = "Team-wide model performance leaderboard";
        tasksSub.innerText = "Team-wide tasks and outcome signals";
      } else {
        roleBadge.className = "px-2.5 py-0.5 text-[11px] font-bold rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm";
        roleBadge.innerHTML = `👤 Developer: ${state.user}`;
        devBanner.classList.remove('hidden');
        adminSection.classList.add('hidden');
        document.getElementById('banner-user-name').innerText = state.user;
        totalCallsSub.innerText = `Traces for ${state.user}`;
        leaderboardSub.innerText = `Models configured and used by ${state.user}`;
        tasksSub.innerText = `Tasks executed by ${state.user}`;
      }
    }

    async function fetchData() {
      try {
        // 1. Health
        const hRes = await fetch('/health');
        const hData = await hRes.json();
        const badge = document.getElementById('health-badge');
        if (hData.ok) {
          badge.className = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800";
          badge.innerHTML = '<span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span> DB Ready';
        } else {
          badge.className = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800";
          badge.innerHTML = '<span class="h-2 w-2 rounded-full bg-rose-400"></span> DB Unready';
        }

        // Prepare Query & Headers
        let headers = {};
        let statsQuery = '';
        let tasksQuery = '';

        if (state.role === 'admin') {
          if (state.adminToken) {
            headers['X-Admin-Token'] = state.adminToken;
            headers['Authorization'] = `Bearer ${state.adminToken}`;
          }
          if (state.filterUser) {
            statsQuery = `?session_id=${encodeURIComponent(state.filterUser)}`;
            tasksQuery = `?session_id=${encodeURIComponent(state.filterUser)}`;
            document.getElementById('active-filter-indicator').innerText = `Filtered: ${state.filterUser} (click to clear)`;
            document.getElementById('active-filter-indicator').onclick = () => { state.filterUser = null; fetchData(); };
          } else {
            document.getElementById('active-filter-indicator').innerText = '';
          }
          // Fetch Admin Connected Developers
          fetchAdminDevelopers(headers);
        } else {
          statsQuery = `?session_id=${encodeURIComponent(state.user)}`;
          tasksQuery = `?session_id=${encodeURIComponent(state.user)}`;
          // Fetch user profile details
          fetchUserProfile(state.user);
        }

        // 2. Fetch Stats
        const sRes = await fetch('/stats' + statsQuery, { headers });
        if (sRes.ok) {
          const stats = await sRes.json();
          renderStats(stats);
        }

        // 3. Fetch Tasks
        const tRes = await fetch('/tasks' + tasksQuery, { headers });
        if (tRes.ok) {
          const tasks = await tRes.json();
          renderTasks(tasks);
        }
      } catch (err) {
        console.error("Dashboard refresh error:", err);
      }
    }

    async function fetchAdminDevelopers(headers) {
      try {
        const res = await fetch('/admin/connected-users', { headers });
        if (res.ok) {
          const data = await res.json();
          renderDevelopers(data.users || []);
        } else if (res.status === 401) {
          console.warn("Admin token invalid or unauthenticated.");
        }
      } catch (e) {
        console.error("Failed to fetch connected developers:", e);
      }
    }

    async function fetchUserProfile(user) {
      try {
        const res = await fetch(`/user/profile?user=${encodeURIComponent(user)}`);
        if (res.ok) {
          const data = await res.json();
          const p = data.profile || {};
          document.getElementById('banner-masked-key').innerText = p.key_masked || 'not-configured';
          document.getElementById('banner-provider').innerText = (p.provider || 'unknown').toUpperCase();
        }
      } catch (e) {
        console.warn("Profile fetch skipped:", e);
      }
    }

    function renderDevelopers(devs) {
      const tbody = document.getElementById('developers-body');
      document.getElementById('connected-count').innerText = `${devs.length} Connected Developer${devs.length === 1 ? '' : 's'}`;

      if (!devs || devs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="py-6 text-center text-slate-500">No developers have connected personal API keys yet.</td></tr>';
        return;
      }

      tbody.innerHTML = '';
      devs.forEach(d => {
        const row = document.createElement('tr');
        row.className = "hover:bg-slate-800/40 transition";
        const models = (d.models_used || []).map(m => `<span class="px-1.5 py-0.5 rounded bg-slate-800 text-[11px] font-mono border border-slate-700">${m}</span>`).join(' ') || '-';
        const lastActive = d.last_seen ? new Date(d.last_seen).toLocaleTimeString() : '-';
        const totalTok = ((d.total_input_tokens || 0) + (d.total_output_tokens || 0)).toLocaleString();

        row.innerHTML = `
          <td class="py-3 px-4 font-semibold text-white flex items-center gap-2">
            <span class="h-6 w-6 rounded-full bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 flex items-center justify-center text-xs font-bold">
              ${(d.session_id || 'U')[0].toUpperCase()}
            </span>
            ${d.session_id}
          </td>
          <td class="py-3 px-4 text-xs text-slate-400 font-mono">${d.project || '-'}</td>
          <td class="py-3 px-4 font-mono text-cyan-400 text-xs font-semibold">${d.key_masked}</td>
          <td class="py-3 px-4 text-xs uppercase font-medium text-slate-300">${d.provider || 'custom'}</td>
          <td class="py-3 px-4 text-xs">${models}</td>
          <td class="py-3 px-4 font-semibold text-slate-100">${(d.total_calls || 0).toLocaleString()}</td>
          <td class="py-3 px-4 text-xs text-slate-400">${totalTok}</td>
          <td class="py-3 px-4 text-xs text-slate-500">${lastActive}</td>
          <td class="py-3 px-4">
            <button onclick="filterByDeveloper('${d.session_id}')" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-indigo-300 rounded text-xs font-medium border border-slate-700 transition">
              Inspect
            </button>
          </td>
        `;
        tbody.appendChild(row);
      });
    }

    function filterByDeveloper(dev) {
      state.filterUser = dev;
      fetchData();
    }

    function renderStats(stats) {
      let totalCalls = 0;
      let totalIn = 0;
      let totalOut = 0;
      let totalPasses = 0;
      let totalFails = 0;
      let totalLatencySum = 0;

      const tbody = document.getElementById('models-body');
      if (!stats || stats.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500">No model usage recorded for this view.</td></tr>';
        document.getElementById('total-calls').innerText = '0';
        document.getElementById('avg-latency').innerText = '-';
        document.getElementById('total-tokens').innerText = '0';
        document.getElementById('token-split').innerText = 'In: 0 | Out: 0';
        document.getElementById('pass-rate').innerText = 'N/A';
        document.getElementById('pass-counts').innerText = '0 passes / 0 fails';
        return;
      }

      tbody.innerHTML = '';
      stats.forEach(m => {
        totalCalls += (m.calls || 0);
        totalIn += (m.input_tokens || 0);
        totalOut += (m.output_tokens || 0);
        totalPasses += (m.passes || 0);
        totalFails += (m.fails || 0);
        totalLatencySum += ((m.avg_latency_ms || 0) * (m.calls || 0));

        const outcomeTotal = (m.passes || 0) + (m.fails || 0);
        const rate = outcomeTotal > 0 ? Math.round((m.passes / outcomeTotal) * 100) : null;
        const rateStr = rate !== null ? `${rate}%` : 'N/A';
        const rateColor = rate >= 70 ? 'text-emerald-400' : (rate >= 40 ? 'text-amber-400' : 'text-slate-400');

        const row = document.createElement('tr');
        row.className = "hover:bg-slate-800/40 transition";
        row.innerHTML = `
          <td class="py-3 px-4 font-mono font-medium text-slate-200 text-xs">${m.model}</td>
          <td class="py-3 px-4 font-semibold text-slate-100">${(m.calls || 0).toLocaleString()}</td>
          <td class="py-3 px-4 text-slate-300">${m.avg_latency_ms ? m.avg_latency_ms + ' ms' : '-'}</td>
          <td class="py-3 px-4 text-slate-400 text-xs">${(m.input_tokens || 0).toLocaleString()}</td>
          <td class="py-3 px-4 text-slate-400 text-xs">${(m.output_tokens || 0).toLocaleString()}</td>
          <td class="py-3 px-4 text-xs"><span class="text-emerald-400 font-semibold">${m.passes || 0}</span> / <span class="text-rose-400 font-semibold">${m.fails || 0}</span></td>
          <td class="py-3 px-4 font-bold ${rateColor}">${rateStr}</td>
        `;
        tbody.appendChild(row);
      });

      document.getElementById('total-calls').innerText = totalCalls.toLocaleString();
      const avgLat = totalCalls > 0 ? Math.round(totalLatencySum / totalCalls) : 0;
      document.getElementById('avg-latency').innerText = `${avgLat} ms`;
      document.getElementById('total-tokens').innerText = (totalIn + totalOut).toLocaleString();
      document.getElementById('token-split').innerText = `In: ${totalIn.toLocaleString()} | Out: ${totalOut.toLocaleString()}`;

      const totalOutcomes = totalPasses + totalFails;
      if (totalOutcomes > 0) {
        const passPercent = Math.round((totalPasses / totalOutcomes) * 100);
        document.getElementById('pass-rate').innerText = `${passPercent}%`;
        document.getElementById('pass-counts').innerText = `${totalPasses} passes / ${totalFails} fails`;
      } else {
        document.getElementById('pass-rate').innerText = 'N/A';
        document.getElementById('pass-counts').innerText = 'No outcomes reported';
      }
    }

    function renderTasks(tasks) {
      const tbody = document.getElementById('tasks-body');
      if (!tasks || tasks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500">No tasks recorded yet for this view.</td></tr>';
        return;
      }
      tbody.innerHTML = '';
      tasks.forEach(t => {
        let badgeClass = "bg-slate-800 text-slate-400 border border-slate-700";
        let statusText = t.latest_outcome || 'in-progress';
        if (['pass', 'accepted'].includes(t.latest_outcome)) {
          badgeClass = "bg-emerald-950 text-emerald-400 border border-emerald-800";
        } else if (['fail', 'rejected'].includes(t.latest_outcome)) {
          badgeClass = "bg-rose-950 text-rose-400 border border-rose-800";
        } else if (t.latest_outcome === 'edited') {
          badgeClass = "bg-amber-950 text-amber-400 border border-amber-800";
        }

        const dateStr = t.created_at ? new Date(t.created_at).toLocaleTimeString() : '-';
        const row = document.createElement('tr');
        row.className = "hover:bg-slate-800/40 transition";
        row.innerHTML = `
          <td class="py-3 px-4 font-mono text-xs font-semibold text-slate-200">${t.task_id}</td>
          <td class="py-3 px-4 text-xs text-slate-400">${t.project || '-'}</td>
          <td class="py-3 px-4 text-xs text-slate-400">${t.task_type || '-'}</td>
          <td class="py-3 px-4 text-xs font-semibold text-slate-200">${t.call_count || 0}</td>
          <td class="py-3 px-4 text-xs font-mono text-slate-300">${t.primary_model || '-'}</td>
          <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-[11px] font-medium uppercase ${badgeClass}">${statusText}</span></td>
          <td class="py-3 px-4 text-xs text-slate-500">${dateStr}</td>
        `;
        tbody.appendChild(row);
      });
    }

    // Modal logic
    function openAccessModal() {
      document.getElementById('access-modal').classList.remove('hidden');
      document.getElementById('access-modal').classList.add('flex');
    }

    function closeAccessModal() {
      document.getElementById('access-modal').classList.add('hidden');
      document.getElementById('access-modal').classList.remove('flex');
    }

    function switchModalTab(tab) {
      if (tab === 'dev') {
        document.getElementById('tab-btn-dev').className = "py-2 rounded-md bg-indigo-600 text-white transition";
        document.getElementById('tab-btn-admin').className = "py-2 rounded-md text-slate-400 hover:text-white transition";
        document.getElementById('modal-tab-dev').classList.remove('hidden');
        document.getElementById('modal-tab-admin').classList.add('hidden');
      } else {
        document.getElementById('tab-btn-dev').className = "py-2 rounded-md text-slate-400 hover:text-white transition";
        document.getElementById('tab-btn-admin').className = "py-2 rounded-md bg-violet-600 text-white transition";
        document.getElementById('modal-tab-dev').classList.add('hidden');
        document.getElementById('modal-tab-admin').classList.remove('hidden');
      }
    }

    function submitDeveloperLogin() {
      const val = document.getElementById('modal-input-user').value.trim() || 'dev';
      state.role = 'dev';
      state.user = val;
      state.adminToken = '';
      state.filterUser = null;
      localStorage.setItem('ao_user', val);
      localStorage.removeItem('ao_admin_token');
      closeAccessModal();
      updateUIForRole();
      fetchData();
    }

    async function submitAdminLogin() {
      const key = document.getElementById('modal-input-admin-key').value.trim();
      if (!key) return;

      // Verify token with backend
      try {
        const res = await fetch('/admin/verify', {
          headers: { 'X-Admin-Token': key, 'Authorization': `Bearer ${key}` }
        });
        if (res.ok) {
          state.role = 'admin';
          state.adminToken = key;
          state.filterUser = null;
          localStorage.setItem('ao_admin_token', key);
          closeAccessModal();
          updateUIForRole();
          fetchData();
        } else {
          alert('Invalid Admin Key or Unauthorized.');
        }
      } catch (e) {
        alert('Could not verify admin key: ' + e);
      }
    }

    initAuth();
    fetchData();
    setInterval(fetchData, 5000);
  </script>
</body>
</html>
"""
