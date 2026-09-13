$ErrorActionPreference = 'Stop'

$workspace = (Get-Location).Path
$appRoot = Join-Path $workspace 'apps/research_os_flutter'
$master = Join-Path $appRoot 'assets/branding/research_os_master.webp'
$windowsRoot = Join-Path $appRoot 'windows'
$icon = Join-Path $windowsRoot 'runner/resources/app_icon.ico'
$brandingScript = Join-Path $workspace 'scripts/apply-research-os-branding.py'

if (-not (Test-Path $master)) {
    throw "Missing canonical Research OS master asset: $master"
}

if (-not (Test-Path $brandingScript)) {
    throw "Missing canonical branding script: $brandingScript"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    throw 'Python is required for canonical branding verification.'
}

$masterHash = (Get-FileHash $master -Algorithm SHA256).Hash

if (-not (Test-Path $windowsRoot)) {
    Write-Host "WINDOWS_BRANDING=skipped"
    Write-Host "WINDOWS_BRANDING_REASON=Research OS Flutter app has no Windows shell."
    Write-Host "RESEARCH_OS_MASTER_SHA256=$masterHash"
    Write-Host "RESEARCH_OS_WINDOWS_BRANDING_GATE=PASS"
    exit 0
}

& $python.Source $brandingScript `
    --master $master `
    --app-root $appRoot `
    --platform windows

if ($LASTEXITCODE -ne 0) {
    throw 'Canonical Research OS Windows branding application failed.'
}

if (-not (Test-Path $icon)) {
    throw "Missing Research OS Windows icon after canonical branding application: $icon"
}

$before = (Get-FileHash $icon -Algorithm SHA256).Hash
$iconBytes = (Get-Item $icon).Length

if ($iconBytes -lt 1000) {
    throw "Research OS Windows icon is unexpectedly small: $iconBytes bytes"
}

& $python.Source $brandingScript `
    --master $master `
    --app-root $appRoot `
    --platform windows

if ($LASTEXITCODE -ne 0) {
    throw 'Canonical Research OS Windows branding re-application failed.'
}

$afterHash = (Get-FileHash $icon -Algorithm SHA256).Hash

if ($afterHash -ne $before) {
    throw 'Research OS Windows icon was not stable after canonical branding application.'
}

Write-Host "RESEARCH_OS_MASTER_SHA256=$masterHash"
Write-Host "RESEARCH_OS_WINDOWS_ICON_SHA256=$afterHash"
Write-Host "RESEARCH_OS_WINDOWS_BRANDING_GATE=PASS"
