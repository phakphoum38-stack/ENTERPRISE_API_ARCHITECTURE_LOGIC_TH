param(
    [switch]$SkipFlutter,
    [switch]$SkipServiceHost
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot

Write-Host "=== Research OS Unified V3 Local Preflight ==="
Write-Host "Repo: $repo"

Push-Location $repo
try {
    Write-Host "`n[1/5] Python compile"
    python -m compileall -q tools/research_os_api tools/research_curator software_factory
    if ($LASTEXITCODE -ne 0) { throw "Python compile failed" }

    Write-Host "`n[2/5] API and Brain Core unit tests"
    $env:RESEARCH_OS_PROVIDER = 'mock'
    $env:RESEARCH_OS_SYNC_KEY = 'local-preflight-key'
    $env:RESEARCH_OS_ALLOW_LEGACY_IDENTITY_HEADERS = '1'
    if (-not $env:RESEARCH_OS_DATA_DIR) {
        $env:RESEARCH_OS_DATA_DIR = Join-Path $env:TEMP 'ResearchOSPreflight'
    }
    $env:RESEARCH_OS_CONVERSATION_STORE = Join-Path $env:RESEARCH_OS_DATA_DIR 'sessions\conversations.json'
    python -m unittest discover -s tools/research_os_api -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "API unit tests failed" }

    Write-Host "`n[3/5] Adaptive Software Factory tests"
    python -m unittest discover -s tests -p "test_adaptive_software_factory*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Adaptive Software Factory tests failed" }

    if (-not $SkipFlutter) {
        Write-Host "`n[4/5] Flutter analyze and tests"
        $flutter = Get-Command flutter -ErrorAction SilentlyContinue
        if (-not $flutter) {
            throw "Flutter is not installed or not available in PATH. Use -SkipFlutter only when intentionally skipping Flutter checks."
        }
        Push-Location (Join-Path $repo 'apps\research_os_flutter')
        try {
            flutter pub get
            if ($LASTEXITCODE -ne 0) { throw "flutter pub get failed" }
            flutter analyze
            if ($LASTEXITCODE -ne 0) { throw "flutter analyze failed" }
            flutter test
            if ($LASTEXITCODE -ne 0) { throw "flutter test failed" }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "`n[4/5] Flutter checks skipped"
    }

    if (-not $SkipServiceHost) {
        Write-Host "`n[5/5] ServiceHost build"
        $dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
        if (-not $dotnet) {
            throw ".NET SDK is not installed or not available in PATH. Use -SkipServiceHost only when intentionally skipping ServiceHost checks."
        }
        dotnet build tools/research_os_service/ResearchOS.ServiceHost.csproj -c Release
        if ($LASTEXITCODE -ne 0) { throw "ServiceHost build failed" }
    }
    else {
        Write-Host "`n[5/5] ServiceHost build skipped"
    }

    Write-Host "`n=== UNIFIED V3 PREFLIGHT PASSED ==="
}
finally {
    Pop-Location
}
