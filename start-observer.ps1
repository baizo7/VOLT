$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $python)) {
    throw "Project Python environment not found: $python"
}
if (-not (Test-Path $envFile)) {
    throw ".env file not found."
}

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

if (-not $env:DATABASE_URL) {
    throw "DATABASE_URL was not loaded from .env."
}

Write-Host "Starting AI Observer on http://127.0.0.1:8787"
& $python -m uvicorn main:app --host 127.0.0.1 --port 8787
