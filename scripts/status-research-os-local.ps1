param(
  [int]$Port = 8787,
  [string]$HealthUrl = "http://127.0.0.1:8787/health"
)

$ErrorActionPreference = "Stop"

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
  Write-Host "Listener : running"
  Write-Host "Port     : $Port"
  Write-Host "PID      : $($listener.OwningProcess)"
} else {
  Write-Host "Listener : stopped"
  Write-Host "Port     : $Port"
}

try {
  $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 3
  Write-Host "Health   : $($health.status)"
  Write-Host "Service  : $($health.service)"
  Write-Host "Version  : $($health.version)"
  exit 0
} catch {
  Write-Host "Health   : unavailable"
  exit 1
}
