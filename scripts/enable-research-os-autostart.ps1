param(
  [string]$DataDir = "$env:USERPROFILE\ResearchOSData"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $RepoRoot "scripts\start-research-os-local.ps1"

if (-not (Test-Path $StartScript)) {
  throw "Research OS start script not found: $StartScript"
}

$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$name = "ResearchOSLocalAPI"
$command = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$StartScript`" -DataDir `"$DataDir`""

New-Item -Path $runKey -Force | Out-Null
New-ItemProperty -Path $runKey -Name $name -Value $command -PropertyType String -Force | Out-Null

Write-Host "Research OS Local API autostart enabled for the current Windows user."
Write-Host "Registry value: $runKey\$name"
Write-Host "Data directory: $DataDir"
