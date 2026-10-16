# VOLT-AI PowerShell CLI Wrapper
# Usage:
#   .\volt.ps1 activate
#   .\volt.ps1 usage
#   .\volt.ps1 dashboard
#   .\volt.ps1 code "Write a python function to add two numbers"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "py"
}
& $python (Join-Path $PSScriptRoot "volt.py") @args
