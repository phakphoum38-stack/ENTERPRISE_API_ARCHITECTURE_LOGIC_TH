param(
  [string]$DataDir = "$env:USERPROFILE\ResearchOSData",
  [string]$HostAddress = "0.0.0.0",
  [int]$Port = 8787,
  [ValidateSet("gemini", "mock", "local", "openai-compatible", "anthropic")]
  [string]$Provider = "gemini"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $RepoRoot "tools\research_os_api"

if (-not (Test-Path $ApiDir)) {
  throw "Research OS API directory not found: $ApiDir"
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "sessions") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "database") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "artifacts") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "backups") | Out-Null

$env:RESEARCH_OS_DATA_DIR = $DataDir
$env:RESEARCH_OS_CONVERSATION_STORE = Join-Path $DataDir "sessions\conversations.json"
$env:RESEARCH_OS_PROVIDER = $Provider
$env:RESEARCH_OS_API_HOST = $HostAddress
$env:RESEARCH_OS_API_PORT = "$Port"
$env:HOST = $HostAddress
$env:PORT = "$Port"

Write-Host ""
Write-Host "Research OS Local API"
Write-Host "Data directory : $DataDir"
Write-Host "Provider       : $Provider"
Write-Host "Local URL      : http://127.0.0.1:$Port"
Write-Host "LAN URL        : http://<WINDOWS-IP>:$Port"
Write-Host ""
Write-Host "Secrets are NOT stored by this script."
Write-Host "Set GEMINI_API_KEY / RESEARCH_OS_GEMINI_API_KEY in your Windows environment when ready."
Write-Host ""

Push-Location $ApiDir
try {
  python render_server.py
}
finally {
  Pop-Location
}
