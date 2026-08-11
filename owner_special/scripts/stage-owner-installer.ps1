param(
    [Parameter(Mandatory=$true)][string]$FlutterReleaseDir,
    [Parameter(Mandatory=$true)][string]$ServiceHostDir,
    [string]$PackageDir = "$PSScriptRoot\..\installer\package"
)
$ErrorActionPreference = 'Stop'
$ownerRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $ownerRoot '..')).Path
$PackageDir = [IO.Path]::GetFullPath($PackageDir)
if (Test-Path $PackageDir) { Remove-Item $PackageDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

function Copy-Tree([string]$Source, [string]$Destination) {
    if (-not (Test-Path $Source)) { throw "Missing package source: $Source" }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Copy-Item (Join-Path $Source '*') $Destination -Recurse -Force
}

Copy-Tree $FlutterReleaseDir (Join-Path $PackageDir 'app')
Copy-Tree $ServiceHostDir (Join-Path $PackageDir 'service_host')
Copy-Tree (Join-Path $ownerRoot 'research_os_friend') (Join-Path $PackageDir 'owner_special\research_os_friend')
Copy-Tree (Join-Path $ownerRoot 'scripts') (Join-Path $PackageDir 'owner_special\scripts')
Copy-Tree (Join-Path $repoRoot 'v3\research_os_v3') (Join-Path $PackageDir 'v3\research_os_v3')
Copy-Item (Join-Path $ownerRoot 'OWNER_MANIFEST.json') (Join-Path $PackageDir 'owner_special\OWNER_MANIFEST.json') -Force

$pythonRoot = (python -c "import sys; print(sys.base_prefix)").Trim()
Copy-Tree $pythonRoot (Join-Path $PackageDir 'runtime\python')
if (-not (Test-Path (Join-Path $PackageDir 'runtime\python\python.exe'))) { throw 'Bundled Python runtime missing' }
if (-not (Get-ChildItem (Join-Path $PackageDir 'app') -Filter 'research_os_owner_special.exe' -Recurse -File -ErrorAction SilentlyContinue)) { throw 'Owner Desktop EXE missing from package' }
if (-not (Test-Path (Join-Path $PackageDir 'service_host\ResearchOS.Owner.ServiceHost.exe'))) { throw 'Owner ServiceHost EXE missing from package' }
Write-Host "Owner Special package staged at $PackageDir"
