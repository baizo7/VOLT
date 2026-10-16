$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $python)) {
    $python = "py"
}
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line -split "=", 2
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()

            if ($value.Length -ge 2 -and
                (($value.StartsWith('"') -and $value.EndsWith('"')) -or
                 ($value.StartsWith("'") -and $value.EndsWith("'")))) {
                $value = $value.Substring(1, $value.Length - 2)
            }

            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

if (-not $env:DATABASE_URL) {
    throw "DATABASE_URL was not loaded from .env."
}

# Fast TCP port probe for PostgreSQL (800ms timeout)
if ($env:DATABASE_URL -match "127\.0\.0\.1:5432|localhost:5432") {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $ar = $tcp.BeginConnect("127.0.0.1", 5432, $null, $null)
    $ok = $ar.AsyncWaitHandle.WaitOne(800)
    if ($ok -and $tcp.Connected) {
        try { $tcp.EndConnect($ar) } catch {}
        $tcp.Close()
        Write-Host "[✓] Local PostgreSQL (port 5432) is online." -ForegroundColor Green
    } else {
        $tcp.Close()
        Write-Host "[!] Local PostgreSQL (port 5432) is not responding." -ForegroundColor Yellow
        try {
            $prevEA = $ErrorActionPreference
            $ErrorActionPreference = "SilentlyContinue"
            docker compose up -d db 2>$null
            $ErrorActionPreference = $prevEA
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[+] Docker container started. Waiting for database..." -ForegroundColor Cyan
                Start-Sleep -Seconds 3
            } else {
                Write-Host "[!] Note: Docker Desktop is not running. Starting VOLT-AI directly." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[!] Note: Docker Desktop is not running. Starting VOLT-AI directly." -ForegroundColor Yellow
        }
    }
}

Write-Host "⚡ Starting VOLT-AI on http://127.0.0.1:8787" -ForegroundColor Cyan
& $python -m uvicorn main:app --host 127.0.0.1 --port 8787
