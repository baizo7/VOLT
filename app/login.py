"""
VOLT-AI — Google Authentication & Login Page
Glassmorphic cyber interface for Google OAuth / Identity Services login
and developer account onboarding into PostgreSQL.
"""
import os

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en" class="h-full bg-[#0a0e1a] text-slate-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sign in to VOLT-AI — Multi-Model Coordination & Observability</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Google Identity Services Library -->
  <script src="https://accounts.google.com/gsi/client" async defer></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700;800;900&display=swap">
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
    body { font-family: 'Inter', sans-serif; background-color: #0a0e1a; }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .glass { background: rgba(15, 20, 36, 0.75); backdrop-filter: blur(16px); }
    .glass-card { background: rgba(15, 20, 36, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(79, 70, 229, 0.25); }
    .glow-indigo { box-shadow: 0 0 50px rgba(79, 70, 229, 0.15); }
    .glow-amber { box-shadow: 0 0 40px rgba(245, 158, 11, 0.15); }
    @keyframes pulseSlow {
      0%, 100% { transform: scale(1); opacity: 0.8; }
      50% { transform: scale(1.05); opacity: 1; }
    }
    .pulse-ambient { animation: pulseSlow 8s ease-in-out infinite; }
  </style>
</head>
<body class="min-h-full flex flex-col justify-between relative overflow-x-hidden selection:bg-indigo-600 selection:text-white">

  <!-- Ambient Glow Effects -->
  <div class="fixed top-[-100px] left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-gradient-to-tr from-indigo-600/20 via-violet-600/15 to-transparent rounded-full blur-[120px] pointer-events-none pulse-ambient"></div>
  <div class="fixed bottom-[-100px] right-[-50px] w-[500px] h-[350px] bg-gradient-to-tl from-amber-500/10 via-amber-600/5 to-transparent rounded-full blur-[100px] pointer-events-none"></div>

  <!-- Top Navigation -->
  <header class="w-full glass border-b border-surface-700/60 px-6 py-3.5 relative z-20">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <a href="/dashboard" class="flex items-center gap-3 group">
        <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-amber-500 via-indigo-600 to-violet-600 flex items-center justify-center font-black text-white text-base shadow-lg shadow-amber-500/20 group-hover:scale-105 transition-transform">⚡</div>
        <div>
          <span class="text-lg font-black tracking-tight text-white"><span class="text-amber-400 font-black">VOLT</span><span class="text-indigo-400 font-black">-AI</span></span>
          <span class="text-[10px] text-slate-400 ml-1.5 px-2 py-0.5 rounded-full bg-surface-800 border border-surface-700 font-semibold">Community Portal</span>
        </div>
      </a>
      <div class="flex items-center gap-3">
        <a href="/dashboard" class="text-xs font-semibold text-slate-400 hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-surface-800">Explore Dashboard</a>
        <a href="https://github.com/baizo7/VOLT" target="_blank" class="text-xs font-semibold text-slate-400 hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-surface-800 flex items-center gap-1.5">
          <svg class="h-4 w-4 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          <span>GitHub</span>
        </a>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-1 max-w-6xl w-full mx-auto px-6 py-10 flex flex-col lg:flex-row items-center justify-center gap-12 relative z-10">
    
    <!-- Left Column: Value Prop & Pitch -->
    <div class="flex-1 max-w-lg space-y-6 text-center lg:text-left">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-700/60 text-indigo-300 text-xs font-semibold">
        <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>Google Account Authentication &bull; Live</span>
      </div>
      
      <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
        Connect & Code with <span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-indigo-400 to-violet-400">VOLT-AI</span>
      </h1>
      
      <p class="text-slate-300 text-base leading-relaxed">
        Sign in with Google to unlock your personal developer workspace, generate live API keys, monitor real-time inference telemetry, and contribute to continuous open model fine-tuning.
      </p>

      <!-- Key Benefits List -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-2">
        <div class="flex items-start gap-3 p-3 rounded-xl bg-surface-900/80 border border-surface-700/60 text-left">
          <div class="h-7 w-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center text-sm font-bold shrink-0">⚡</div>
          <div>
            <h4 class="text-xs font-bold text-white">Free Starter Tier</h4>
            <p class="text-[11px] text-slate-400 mt-0.5">30-50 free daily calls to the coordinated model.</p>
          </div>
        </div>

        <div class="flex items-start gap-3 p-3 rounded-xl bg-surface-900/80 border border-surface-700/60 text-left">
          <div class="h-7 w-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-sm font-bold shrink-0">🔑</div>
          <div>
            <h4 class="text-xs font-bold text-white">Live API Keys</h4>
            <p class="text-[11px] text-slate-400 mt-0.5">1-click key for Cursor, VS Code, and Python SDK.</p>
          </div>
        </div>

        <div class="flex items-start gap-3 p-3 rounded-xl bg-surface-900/80 border border-surface-700/60 text-left">
          <div class="h-7 w-7 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-sm font-bold shrink-0">📊</div>
          <div>
            <h4 class="text-xs font-bold text-white">Personal Telemetry</h4>
            <p class="text-[11px] text-slate-400 mt-0.5">Private dashboard metrics for latency & tokens.</p>
          </div>
        </div>

        <div class="flex items-start gap-3 p-3 rounded-xl bg-surface-900/80 border border-surface-700/60 text-left">
          <div class="h-7 w-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold shrink-0">🛡️</div>
          <div>
            <h4 class="text-xs font-bold text-white">Zero-Leak Privacy</h4>
            <p class="text-[11px] text-slate-400 mt-0.5">Automatic in-flight scrubbing of all secrets.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Column: Login Card -->
    <div class="w-full max-w-md">
      <div class="glass-card glow-indigo rounded-2xl p-7 md:p-8 space-y-6 shadow-2xl relative">
        
        <!-- Header in Card -->
        <div class="text-center space-y-1.5">
          <div class="mx-auto h-12 w-12 rounded-2xl bg-gradient-to-tr from-amber-500 via-indigo-600 to-violet-600 flex items-center justify-center text-2xl font-black text-white shadow-lg shadow-indigo-500/25">⚡</div>
          <h2 class="text-2xl font-black text-white tracking-tight pt-2">Developer Sign In</h2>
          <p class="text-xs text-slate-400">Authenticate with your Google account</p>
        </div>

        <!-- Notification Banner -->
        <div id="login-alert" class="hidden px-3.5 py-2.5 rounded-xl text-xs font-medium border flex items-center gap-2"></div>

        <!-- Google Official Sign-In Button Container -->
        <div class="space-y-4 pt-1">
          <div class="flex flex-col items-center justify-center">
            <!-- Google Identity Services Element -->
            <div id="g_id_onload"
                 data-context="signin"
                 data-ux_mode="popup"
                 data-callback="handleGoogleCredentialResponse"
                 data-auto_prompt="false">
            </div>
            <div id="google-signin-btn-wrapper" class="flex justify-center w-full min-h-[44px]">
              <!-- Google Identity button rendered by JS -->
              <div id="google-btn-container"></div>
            </div>
          </div>

          <div class="relative flex items-center justify-center my-4">
            <div class="border-t border-surface-700 w-full"></div>
            <span class="bg-surface-900 px-3 text-[10px] text-slate-500 uppercase tracking-wider font-semibold absolute">or quick access</span>
          </div>

          <!-- Instant Demo Developer Sign-In (Available without configuring Google Cloud Console) -->
          <div class="space-y-2.5">
            <button onclick="handleDemoLogin()" id="btn-demo-login" class="w-full py-2.5 px-4 bg-surface-800 hover:bg-surface-700 border border-surface-600 text-white rounded-xl text-xs font-semibold transition flex items-center justify-center gap-2 group shadow-sm">
              <span class="text-base group-hover:scale-110 transition-transform">🚀</span>
              <span>1-Click Sign In as Developer (Instant Demo)</span>
            </button>

            <!-- Custom Developer Name / Email input -->
            <div class="pt-2">
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Or enter developer email to save profile:</label>
              <div class="flex items-center gap-2">
                <input type="email" id="custom-email-input" placeholder="developer@gmail.com" class="flex-1 bg-surface-950/80 border border-surface-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono">
                <button onclick="handleCustomEmailLogin()" class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition shrink-0 shadow-sm">
                  Sign In
                </button>
              </div>
            </div>
          </div>

          <!-- Admin Key Toggle -->
          <div class="pt-3 border-t border-surface-700/60 text-center">
            <button onclick="toggleAdminPanel()" class="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold transition inline-flex items-center gap-1">
              <span>👑 Administrator Access</span>
              <span id="admin-arrow">▼</span>
            </button>
            <div id="admin-login-drawer" class="hidden mt-3 p-3 rounded-xl bg-surface-950/80 border border-surface-700 text-left space-y-2.5">
              <label class="block text-[10px] uppercase font-bold text-violet-400 tracking-wider">Admin Secret Key</label>
              <input type="password" id="admin-key-input" placeholder="Enter VOLT_ADMIN_KEY..." class="w-full bg-surface-900 border border-surface-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-violet-500 font-mono">
              <button onclick="handleAdminLogin()" class="w-full py-2 bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold rounded-lg transition shadow-sm">
                Unlock Admin Console
              </button>
            </div>
          </div>

        </div>

        <!-- Privacy & Attribution Note -->
        <div class="text-center pt-2">
          <p class="text-[11px] text-slate-500">
            By signing in, your developer profile and activity are securely stored in PostgreSQL under Baizo's VOLT-AI platform.
          </p>
        </div>

      </div>
    </div>

  </main>

  <!-- Footer -->
  <footer class="w-full border-t border-surface-800/80 py-4 px-6 text-center text-xs text-slate-500 relative z-10">
    <div class="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
      <p>Powered by <strong class="text-slate-300">VOLT-AI</strong> &bull; Created by <a href="https://github.com/baizo7" target="_blank" class="text-indigo-400 hover:underline font-semibold">Baizo (S Sanjai)</a></p>
      <p class="text-[11px] text-slate-600">Platform Proprietary &bull; Models Open Source (Apache 2.0)</p>
    </div>
  </footer>

  <!-- Client JavaScript for Google OAuth & Session Handling -->
  <script>
    const GOOGLE_CLIENT_ID = "{{GOOGLE_CLIENT_ID}}";

    function showAlert(msg, isError = false) {
      const el = document.getElementById('login-alert');
      el.className = isError
        ? "px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-rose-950/70 border border-rose-800 text-rose-300 flex items-center gap-2"
        : "px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-950/70 border border-emerald-800 text-emerald-300 flex items-center gap-2";
      el.innerHTML = (isError ? "⚠️ " : "✅ ") + msg;
      el.classList.remove('hidden');
    }

    // Initialize Google Identity Services if client ID is configured
    window.onload = function() {
      if (GOOGLE_CLIENT_ID && GOOGLE_CLIENT_ID !== "{{GOOGLE_CLIENT_ID}}" && GOOGLE_CLIENT_ID.length > 5) {
        try {
          if (window.google && google.accounts && google.accounts.id) {
            google.accounts.id.initialize({
              client_id: GOOGLE_CLIENT_ID,
              callback: handleGoogleCredentialResponse,
              auto_select: false,
            });
            google.accounts.id.renderButton(
              document.getElementById("google-btn-container"),
              {
                theme: "filled_blue",
                size: "large",
                shape: "pill",
                text: "signin_with",
                width: 320,
              }
            );
          }
        } catch(e) {
          console.warn("Google Identity Init error:", e);
        }
      } else {
        // Fallback UI when GOOGLE_CLIENT_ID is not configured yet
        const container = document.getElementById("google-btn-container");
        container.innerHTML = `
          <button onclick="handleGooglePromptClick()" class="w-[320px] py-2.5 px-4 rounded-full bg-white hover:bg-slate-100 text-slate-800 font-semibold text-xs transition flex items-center justify-center gap-3 shadow-md border border-slate-300">
            <svg class="h-4 w-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
              <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
              <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 10.03 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
              <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
            </svg>
            <span>Sign in with Google</span>
          </button>
        `;
      }
    };

    function handleGooglePromptClick() {
      // If GOOGLE_CLIENT_ID isn't set in environment, guide the user or proceed with instant sign-in
      const promptEmail = prompt("Enter your Google Account email to sign in:", "developer@gmail.com");
      if (promptEmail && promptEmail.trim()) {
        loginWithProfile({
          email: promptEmail.trim(),
          name: promptEmail.split('@')[0],
          provider: "google"
        });
      }
    }

    // Handler when Google Identity returns an ID token
    async function handleGoogleCredentialResponse(response) {
      if (!response || !response.credential) {
        showAlert("Failed to receive Google credential", true);
        return;
      }
      try {
        showAlert("Verifying with Google...", false);
        const res = await fetch("/api/auth/google/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ credential: response.credential })
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          saveSessionAndRedirect(data);
        } else {
          showAlert(data.error || "Google authentication failed", true);
        }
      } catch(err) {
        showAlert("Connection error: " + err, true);
      }
    }

    // 1-Click Demo Login
    async function handleDemoLogin() {
      loginWithProfile({
        email: "developer@volt.ai",
        name: "Volt Developer",
        picture: "https://lh3.googleusercontent.com/a/default-user"
      });
    }

    // Custom Email Login
    async function handleCustomEmailLogin() {
      const emailInput = document.getElementById('custom-email-input');
      const email = emailInput ? emailInput.value.trim() : '';
      if (!email || !email.includes('@')) {
        showAlert("Please enter a valid email address", true);
        return;
      }
      loginWithProfile({
        email: email,
        name: email.split('@')[0],
      });
    }

    async function loginWithProfile(profile) {
      try {
        showAlert("Signing in and registering user in database...", false);
        const res = await fetch("/api/auth/demo-login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(profile)
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          saveSessionAndRedirect(data);
        } else {
          showAlert(data.error || "Sign in failed", true);
        }
      } catch(err) {
        showAlert("Connection error: " + err, true);
      }
    }

    // Administrator Secret Key Login
    async function handleAdminLogin() {
      const key = document.getElementById('admin-key-input').value.trim();
      if (!key) {
        showAlert("Please enter your admin key", true);
        return;
      }
      try {
        const res = await fetch("/admin/verify", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Token": key,
            "Authorization": "Bearer " + key
          },
          body: JSON.stringify({ admin_key: key })
        });
        const data = await res.json();
        if (res.ok && data.ok && data.role === "admin") {
          localStorage.setItem("ao_admin_token", key);
          localStorage.setItem("ao_role", "admin");
          showAlert("Admin key validated! Redirecting to Dashboard...", false);
          setTimeout(() => { window.location.href = "/dashboard?admin_token=" + encodeURIComponent(key); }, 600);
        } else {
          showAlert("Invalid Administrator Key", true);
        }
      } catch(err) {
        showAlert("Error connecting to admin auth: " + err, true);
      }
    }

    function saveSessionAndRedirect(data) {
      const u = data.user || {};
      const token = data.token || "";
      if (token) localStorage.setItem("ao_session_token", token);
      if (u.email) localStorage.setItem("ao_user", u.email);
      if (u.name) localStorage.setItem("ao_user_name", u.name);
      if (u.picture) localStorage.setItem("ao_user_pic", u.picture);
      if (u.role) localStorage.setItem("ao_role", u.role);

      showAlert(`Welcome, ${u.name || u.email}! Saved to database. Redirecting...`, false);
      setTimeout(() => {
        window.location.href = data.redirect_url || "/dashboard";
      }, 700);
    }

    function toggleAdminPanel() {
      const d = document.getElementById('admin-login-drawer');
      const arrow = document.getElementById('admin-arrow');
      d.classList.toggle('hidden');
      arrow.textContent = d.classList.contains('hidden') ? '▼' : '▲';
    }
  </script>
</body>
</html>
"""


def get_login_html(google_client_id: str = "") -> str:
    """Render login page with configured Google Client ID."""
    cid = google_client_id or os.environ.get("GOOGLE_CLIENT_ID", "")
    return LOGIN_HTML.replace("{{GOOGLE_CLIENT_ID}}", cid)
