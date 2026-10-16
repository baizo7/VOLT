# ObserverCoder-1.0 PowerShell CLI Wrapper
# Usage:
#   .\observer-coder.ps1 "Write a python function to add two numbers"
#   .\observer-coder.ps1 chat
#   .\observer-coder.ps1 models
#   .\observer-coder.ps1 code -f main.py "Explain this file"

$python = "py"
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    $python = "python"
}

& $python (Join-Path $PSScriptRoot "observer-coder.py") @args
