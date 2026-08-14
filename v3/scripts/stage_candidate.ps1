param(
    [Parameter(Mandatory = $true)]
    [string]$FlutterReleaseDir,

    [Parameter(Mandatory = $true)]
    [string]$ServiceHostDir,

    [Parameter(Mandatory = $true)]
    [string]$FlutterIconPath
)

$ErrorActionPreference = 'Stop'

$v3Root = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $v3Root
$ownerRoot = Join-Path $repoRoot 'owner_special'
$installerRoot = Join-Path $v3Root 'installer'
$package = Join-Path $installerRoot 'package'

if (Test-Path $package) {
    Remove-Item $package -Recurse -Force
}
New-Item -ItemType Directory -Path $package -Force | Out-Null

$appDir = Join-Path $package 'app'
$serviceDir = Join-Path $package 'service'
$packagedV3 = Join-Path $package 'v3'
$packagedScripts = Join-Path $package 'scripts'
$packagedOwner = Join-Path $package 'owner_special'

New-Item -ItemType Directory -Path $appDir -Force | Out-Null
New-Item -ItemType Directory -Path $serviceDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packagedV3 'scripts') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packagedV3 'runtime\python') -Force | Out-Null
New-Item -ItemType Directory -Path $packagedScripts -Force | Out-Null
New-Item -ItemType Directory -Path $packagedOwner -Force | Out-Null

Copy-Item (Join-Path $FlutterReleaseDir '*') $appDir -Recurse -Force
Copy-Item (Join-Path $ServiceHostDir '*') $serviceDir -Recurse -Force
Copy-Item (Join-Path $v3Root 'research_os_v3') $packagedV3 -Recurse -Force
Copy-Item (Join-Path $v3Root 'scripts\run_service.py') (Join-Path $packagedV3 'scripts\run_service.py') -Force
Copy-Item (Join-Path $v3Root 'scripts\v3-service.ps1') (Join-Path $packagedScripts 'v3-service.ps1') -Force

# Keep the Owner Friend brain source and provenance in the Unified package without
# changing its existing service registration or port. V3 remains the active 8788
# coordination authority for this candidate.
if (Test-Path (Join-Path $ownerRoot 'research_os_friend')) {
    Copy-Item (Join-Path $ownerRoot 'research_os_friend') $packagedOwner -Recurse -Force
}
if (Test-Path (Join-Path $ownerRoot 'OWNER_MANIFEST.json')) {
    Copy-Item (Join-Path $ownerRoot 'OWNER_MANIFEST.json') (Join-Path $packagedOwner 'OWNER_MANIFEST.json') -Force
}

$pythonRoot = (& python -c "import sys; print(sys.base_prefix)").Trim()
if (-not (Test-Path (Join-Path $pythonRoot 'python.exe') -PathType Leaf)) {
    throw "Python runtime root not found: $pythonRoot"
}
Copy-Item (Join-Path $pythonRoot '*') (Join-Path $packagedV3 'runtime\python') -Recurse -Force

if (-not (Test-Path $FlutterIconPath -PathType Leaf)) {
    throw "Flutter icon was not generated: $FlutterIconPath"
}
Copy-Item $FlutterIconPath (Join-Path $installerRoot 'research_os_v3.ico') -Force

$sha = if ($env:GITHUB_SHA) { $env:GITHUB_SHA } else { 'local' }
Set-Content -Path (Join-Path $package 'BUILD_SHA.txt') -Value $sha -Encoding utf8

$required = @(
    (Join-Path $appDir 'research_os_v3_flutter.exe'),
    (Join-Path $serviceDir 'ResearchOS.V3.ServiceHost.exe'),
    (Join-Path $packagedV3 'runtime\python\python.exe'),
    (Join-Path $packagedV3 'research_os_v3\__init__.py'),
    (Join-Path $packagedV3 'scripts\run_service.py'),
    (Join-Path $packagedScripts 'v3-service.ps1'),
    (Join-Path $packagedOwner 'OWNER_MANIFEST.json'),
    (Join-Path $packagedOwner 'research_os_friend\__init__.py')
)
foreach ($path in $required) {
    if (-not (Test-Path $path -PathType Leaf)) {
        throw "Candidate package is incomplete: $path"
    }
}

$files = @(Get-ChildItem $package -File -Recurse)
$bytes = ($files | Measure-Object -Property Length -Sum).Sum
Write-Host "Staged Research OS 3.2 Unified candidate package: files=$($files.Count) bytes=$bytes"
