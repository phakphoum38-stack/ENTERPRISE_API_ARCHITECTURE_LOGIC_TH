param(
  [string]$DataDir = "$env:USERPROFILE\ResearchOSData",
  [string]$BackupDir = "$env:USERPROFILE\ResearchOSData\backups"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $DataDir)) {
  throw "Research OS data directory not found: $DataDir"
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$archive = Join-Path $BackupDir "research-os-$stamp.zip"

$items = Get-ChildItem -Force $DataDir | Where-Object { $_.FullName -ne $BackupDir }
if (-not $items) {
  throw "No Research OS data found to back up."
}

Compress-Archive -Path $items.FullName -DestinationPath $archive -CompressionLevel Optimal

Write-Host "Research OS backup completed."
Write-Host "Archive: $archive"
