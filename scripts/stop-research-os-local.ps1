param(
  [int]$Port = 8787,
  [string]$PidFile = "$env:USERPROFILE\ResearchOSData\run\research-os-api.pid"
)

$ErrorActionPreference = "Stop"

if (Test-Path $PidFile) {
  $rawPid = (Get-Content $PidFile -Raw).Trim()
  $pidValue = 0
  if ([int]::TryParse($rawPid, [ref]$pidValue)) {
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
      Stop-Process -Id $pidValue -Force
      Write-Host "Research OS Local API stopped (PID $pidValue)."
    }
  }
  Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

$connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($connection in $connections) {
  $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
  if ($process -and $process.ProcessName -match 'python') {
    Stop-Process -Id $connection.OwningProcess -Force
    Write-Host "Stopped Python listener on port $Port (PID $($connection.OwningProcess))."
  }
}

Write-Host "Research OS Local API is not listening on port $Port."
