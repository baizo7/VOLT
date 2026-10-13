# AI Observer PowerShell CLI Wrapper
# Usage:
#   .\observer.ps1 activate
#   .\observer.ps1 usage
#   .\observer.ps1 dashboard
#   .\observer.ps1 test

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python (Join-Path $PSScriptRoot "observer.py") @args
