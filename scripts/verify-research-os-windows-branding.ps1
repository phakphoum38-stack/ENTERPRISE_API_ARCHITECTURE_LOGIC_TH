$ErrorActionPreference = 'Stop'

$workspace = (Get-Location).Path
$master = Join-Path $workspace 'assets/branding/research_os_master.webp'
$icon = Join-Path $workspace 'apps/research_os_flutter/windows/runner/resources/app_icon.ico'

if (-not (Test-Path $master)) { throw "Missing canonical Research OS master asset: $master" }
if (-not (Test-Path $icon)) { throw "Missing Research OS Windows icon: $icon" }

$masterHash = (Get-FileHash $master -Algorithm SHA256).Hash
$iconHash = (Get-FileHash $icon -Algorithm SHA256).Hash
$iconBytes = (Get-Item $icon).Length

if ($iconBytes -lt 1000) { throw "Research OS Windows icon is unexpectedly small: $iconBytes bytes" }

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) { throw 'Python is required for canonical branding verification.' }

$brandingScript = Join-Path $workspace 'scripts/apply-research-os-branding.py'
if (-not (Test-Path $brandingScript)) { throw "Missing canonical branding script: $brandingScript" }

$before = $iconHash
& $python.Source $brandingScript --master $master --root $workspace
if ($LASTEXITCODE -ne 0) { throw 'Canonical Research OS branding application failed.' }

$afterHash = (Get-FileHash $icon -Algorithm SHA256).Hash
if ($afterHash -ne $before) {
  throw 'Research OS Windows icon was not stable after canonical branding application.'
}

Write-Host "RESEARCH_OS_MASTER_SHA256=$masterHash"
Write-Host "RESEARCH_OS_WINDOWS_ICON_SHA256=$afterHash"
Write-Host "RESEARCH_OS_WINDOWS_BRANDING_GATE=PASS"
