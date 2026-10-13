"""
Interactive analytics dashboard template for AI Model Observer.
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
  </style>
</head>
<body class="min-h-full flex flex-col p-6 max-w-7xl mx-auto space-y-6">
  <!-- Top Navigation & Health Status -->
  <header class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
    <div class="flex items-center space-x-3">
      <div class="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
        AO
      </div>
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">AI Model Observer</h1>
        <p class="text-xs text-slate-400">Capture Proxy &bull; Model Performance Analytics</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <span id="health-badge" class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
        <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
        Connecting...
      </span>
      <button id="refresh-btn" onclick="fetchData()" class="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md border border-slate-700 transition">
        Refresh Now
      </button>
    </div>
  </header>

  <!-- Metrics Grid -->
  <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
      <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Calls</span>
      <p id="total-calls" class="text-2xl font-bold text-white mt-1">-</p>
      <span class="text-[11px] text-slate-500">Proxied LLM traces</span>
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

  <!-- Model Performance Leaderboard -->
  <section class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
    <div class="p-4 border-b border-slate-800 flex justify-between items-center">
      <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wider">Model Performance Leaderboard</h2>
      <span class="text-xs text-slate-400">Last-touch outcome attribution</span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-slate-300">
        <thead class="bg-slate-950/50 text-xs text-slate-400 border-b border-slate-800 uppercase">
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

  <!-- Recent Tasks -->
  <section class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
    <div class="p-4 border-b border-slate-800 flex justify-between items-center">
      <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wider">Recent Tasks & Outcomes</h2>
      <span class="text-xs text-slate-400">Latest active sessions</span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-slate-300">
        <thead class="bg-slate-950/50 text-xs text-slate-400 border-b border-slate-800 uppercase">
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

  <footer class="pt-4 border-t border-slate-800/80 text-xs text-slate-500 flex justify-between items-center">
    <span>AI Model Observer &bull; Phase 2</span>
    <span>Auto-refreshes every 5s</span>
  </footer>

  <script>
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token') || '';
    const authQuery = token ? `?token=${encodeURIComponent(token)}` : '';
    const headers = token ? { 'X-Observer-Token': token } : {};

    async function fetchData() {
      try {
        // Health
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

        // Stats
        const sRes = await fetch('/stats' + authQuery, { headers });
        if (sRes.ok) {
          const stats = await sRes.json();
          renderStats(stats);
        }

        // Tasks
        const tRes = await fetch('/tasks' + authQuery, { headers });
        if (tRes.ok) {
          const tasks = await tRes.json();
          renderTasks(tasks);
        }
      } catch (err) {
        console.error("Dashboard refresh error:", err);
      }
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
        tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500">No model calls recorded yet.</td></tr>';
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
        tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500">No tasks recorded yet.</td></tr>';
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

    fetchData();
    setInterval(fetchData, 5000);
  </script>
</body>
</html>
"""
