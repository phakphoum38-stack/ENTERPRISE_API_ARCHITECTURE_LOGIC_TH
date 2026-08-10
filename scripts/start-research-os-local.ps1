param(
  [string]$DataDir = "$env:USERPROFILE\ResearchOSData",
  [string]$HostAddress = "127.0.0.1",
  [int]$Port = 8787,
  [ValidateSet("gemini", "mock", "local", "openai-compatible", "anthropic")]
  [string]$Provider = "gemini",
  [switch]$Background
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $RepoRoot "tools\research_os_api"
$RunDir = Join-Path $DataDir "run"
$LogDir = Join-Path $DataDir "logs"
$PidFile = Join-Path $RunDir "research-os-api.pid"
$OutLog = Join-Path $LogDir "research-os-api.out.log"
$ErrLog = Join-Path $LogDir "research-os-api.err.log"

if (-not (Test-Path $ApiDir)) {
  throw "Research OS API directory not found: $ApiDir"
}

@(
  $DataDir,
  (Join-Path $DataDir "sessions"),
  (Join-Path $DataDir "database"),
  (Join-Path $DataDir "artifacts"),
  (Join-Path $DataDir "backups"),
  $RunDir,
  $LogDir
) | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }

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
Write-Host "Bind address   : $HostAddress"
Write-Host "Local URL      : http://127.0.0.1:$Port"
if ($HostAddress -ne "127.0.0.1" -and $HostAddress -ne "localhost" -and $HostAddress -ne "::1") {
  Write-Host "Exposed mode   : signed identity is required for protected API routes"
}
Write-Host ""
Write-Host "Secrets are NOT stored by this script."
Write-Host "Set GEMINI_API_KEY / RESEARCH_OS_GEMINI_API_KEY in your Windows environment when ready."
Write-Host ""

if ($Background) {
  if (Test-Path $PidFile) {
    $existingPidText = (Get-Content $PidFile -Raw).Trim()
    $existingPid = 0
    if ([int]::TryParse($existingPidText, [ref]$existingPid)) {
      $existing = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
      if ($existing) {
        Write-Host "Research OS Local API is already running (PID $existingPid)."
        exit 0
      }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
  }

  $startArgs = @{
    FilePath = "python"
    ArgumentList = "render_server.py"
    WorkingDirectory = $ApiDir
    WindowStyle = "Hidden"
    RedirectStandardOutput = $OutLog
    RedirectStandardError = $ErrLog
    PassThru = $true
  }
  $process = Start-Process @startArgs
  Set-Content -Path $PidFile -Value $process.Id -NoNewline
  Write-Host "Research OS Local API started in background (PID $($process.Id))."
  Write-Host "PID file : $PidFile"
  Write-Host "Logs     : $LogDir"
  exit 0
}

Push-Location $ApiDir
try {
  python render_server.py
}
finally {
  Pop-Location
}
