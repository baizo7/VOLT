$ErrorActionPreference = "Stop"

$settingsPath = Join-Path $HOME ".gemini\antigravity-cli\settings.json"
$runBackupPath = "$settingsPath.observer-run-$PID.bak"

$oldGeminiKey = $env:GEMINI_API_KEY
$oldBaseUrl = $env:GOOGLE_GEMINI_BASE_URL
$backupCreated = $false

try {
    # Confirm Observer is ready before touching settings.
    $health = Invoke-RestMethod `
        -Uri "http://127.0.0.1:8787/health" `
        -TimeoutSec 5

    if (-not $health.ok -or $health.status -ne "ready") {
        throw "AI Observer is not ready. Start Observer first."
    }

    if (-not (Test-Path -LiteralPath $settingsPath)) {
        throw "Antigravity settings file not found. No changes made."
    }

    if (Test-Path -LiteralPath $runBackupPath) {
        throw "Temporary backup already exists. No changes made: $runBackupPath"
    }

    # Back up the current settings for this run only.
    Copy-Item -LiteralPath $settingsPath -Destination $runBackupPath
    $backupCreated = $true

    # Switch only the model provider for this temporary session.
    $settings = Get-Content -LiteralPath $settingsPath -Raw |
        ConvertFrom-Json

    if ($settings.PSObject.Properties.Name -contains "modelProvider") {
        $settings.modelProvider = "gemini"
    } else {
        $settings | Add-Member `
            -NotePropertyName "modelProvider" `
            -NotePropertyValue "gemini"
    }

    $json = $settings | ConvertTo-Json -Depth 30

    [System.IO.File]::WriteAllText(
        $settingsPath,
        $json,
        [System.Text.UTF8Encoding]::new($false)
    )

    # Prompt privately if no key is already available.
    if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
        $secureKey = Read-Host "Enter Gemini API key (hidden input)" -AsSecureString
        $env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
        Remove-Variable secureKey
    }

    if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
        throw "No Gemini API key was provided."
    }

    $env:GOOGLE_GEMINI_BASE_URL = "http://127.0.0.1:8787"

    Write-Host ""
    Write-Host "Starting Antigravity through AI Observer."
    Write-Host "Exit Antigravity normally to restore your settings."
    Write-Host ""

    & agy
}
finally {
    # Restore the exact settings file saved for this run.
    if ($backupCreated -and (Test-Path -LiteralPath $runBackupPath)) {
        try {
            Copy-Item -LiteralPath $runBackupPath `
                -Destination $settingsPath -Force

            Remove-Item -LiteralPath $runBackupPath -Force
            Write-Host "Original settings restored."
        } catch {
            Write-Warning "Could not restore settings automatically."
            Write-Warning "Your temporary backup is retained at: $runBackupPath"
            Write-Warning "Restore it manually before launching Antigravity normally."
        }
    }

    # Restore this process's previous environment values.
    if ($null -eq $oldGeminiKey) {
        Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
    } else {
        $env:GEMINI_API_KEY = $oldGeminiKey
    }

    if ($null -eq $oldBaseUrl) {
        Remove-Item Env:GOOGLE_GEMINI_BASE_URL -ErrorAction SilentlyContinue
    } else {
        $env:GOOGLE_GEMINI_BASE_URL = $oldBaseUrl
    }
}
