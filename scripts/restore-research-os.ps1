param(
  [Parameter(Mandatory = $true)]
  [string]$Archive,
  [string]$DataDir = "$env:USERPROFILE\ResearchOSData"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Archive)) {
  throw "Backup archive not found: $Archive"
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

Write-Host "This will restore Research OS data into: $DataDir"
Write-Host "Existing files with the same names may be replaced."

Expand-Archive -Path $Archive -DestinationPath $DataDir -Force

Write-Host "Research OS restore completed."
Write-Host "Data directory: $DataDir"
