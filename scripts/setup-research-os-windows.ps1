param(
  [string]$Root = "$env:USERPROFILE\ResearchOS",
  [string]$DataDir = "$env:USERPROFILE\ResearchOSData"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Research OS Desktop Foundation"
Write-Host "Repository : $RepoRoot"
Write-Host "Root       : $Root"
Write-Host "Data       : $DataDir"

$directories = @(
  $Root,
  $DataDir,
  (Join-Path $DataDir "database"),
  (Join-Path $DataDir "sessions"),
  (Join-Path $DataDir "artifacts"),
  (Join-Path $DataDir "embeddings"),
  (Join-Path $DataDir "cache"),
  (Join-Path $DataDir "backups"),
  (Join-Path $DataDir "logs")
)

foreach ($directory in $directories) {
  New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

[Environment]::SetEnvironmentVariable("RESEARCH_OS_DATA_DIR", $DataDir, "User")
[Environment]::SetEnvironmentVariable(
  "RESEARCH_OS_CONVERSATION_STORE",
  (Join-Path $DataDir "sessions\conversations.json"),
  "User"
)
[Environment]::SetEnvironmentVariable("RESEARCH_OS_API_HOST", "0.0.0.0", "User")
[Environment]::SetEnvironmentVariable("RESEARCH_OS_API_PORT", "8787", "User")

Write-Host ""
Write-Host "Local-first folders are ready."
Write-Host "Persistent user environment variables were created."
Write-Host "No AI/API secret was written by this setup script."
Write-Host ""
Write-Host "Next:"
Write-Host "  .\scripts\start-research-os-local.ps1 -DataDir `"$DataDir`""
Write-Host ""
Write-Host "Health: http://127.0.0.1:8787/health"
