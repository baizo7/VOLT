# VOLT-AI Coder PowerShell CLI Wrapper
# Usage:
#   .\volt-coder.ps1 "Write a python function to add two numbers"
#   .\volt-coder.ps1 chat
#   .\volt-coder.ps1 models
#   .\volt-coder.ps1 code -f main.py "Explain this file"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "py"
}
& $python (Join-Path $PSScriptRoot "volt-coder.py") @args
