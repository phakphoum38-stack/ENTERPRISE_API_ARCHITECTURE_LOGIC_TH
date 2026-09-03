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

Write-Host 'Installing Owner runtime Python dependencies required by Launch Desk...'
python -m pip install --disable-pip-version-check --quiet 'openai-agents>=0.21.0,<1.0'
if ($LASTEXITCODE -ne 0) { throw 'OpenAI Agents SDK installation failed' }

$pythonRoot = (python -c "import sys; print(sys.base_prefix)").Trim()
Copy-Tree $pythonRoot (Join-Path $PackageDir 'runtime\python')
if (-not (Test-Path (Join-Path $PackageDir 'runtime\python\python.exe'))) { throw 'Bundled Python runtime missing' }

$ownerExe = Join-Path $PackageDir 'app\Research OS Friend.exe'
if (-not (Test-Path $ownerExe -PathType Leaf)) { throw 'Canonical Owner Desktop EXE missing from package: Research OS Friend.exe' }
& (Join-Path $ownerRoot 'scripts\verify-owner-build-identity.ps1') -ExePath $ownerExe -ExpectedManifestPath (Join-Path $PackageDir 'owner_special\OWNER_MANIFEST.json')
if ($LASTEXITCODE -ne 0) { throw 'Owner Desktop Build Identity Gate failed during packaging' }

if (-not (Test-Path (Join-Path $PackageDir 'service_host\ResearchOS.Owner.ServiceHost.exe'))) { throw 'Owner ServiceHost EXE missing from package' }
Write-Host "Owner Special package staged at $PackageDir"
