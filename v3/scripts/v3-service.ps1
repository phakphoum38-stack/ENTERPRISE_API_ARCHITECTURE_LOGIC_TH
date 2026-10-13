param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('install', 'uninstall')]
    [string]$Action,

    [string]$ServiceName = 'ResearchOSV3Service',
    [int]$Port = 8788
)

$ErrorActionPreference = 'Stop'

if ($Port -lt 1 -or $Port -gt 65535) {
    throw "Port must be between 1 and 65535: $Port"
}

$appRoot = Split-Path -Parent $PSScriptRoot
$serviceExe = Join-Path $appRoot 'service\ResearchOS.V3.ServiceHost.exe'
$v3Root = Join-Path $appRoot 'v3'
$pythonExe = Join-Path $v3Root 'runtime\python\python.exe'
$dataDir = Join-Path $env:ProgramData 'ResearchOSV3'

function Remove-V3Service {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -ne 'Stopped') {
            Stop-Service -Name $ServiceName -Force -ErrorAction Stop
            $service = Get-Service -Name $ServiceName -ErrorAction Stop
            $service.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(20))
        }
        $deleteOutput = sc.exe delete $ServiceName 2>&1
        if ($LASTEXITCODE -ne 0 -and ($deleteOutput -join ' ') -notmatch 'marked for deletion') {
            throw "Failed to delete V3 service '$ServiceName': $($deleteOutput -join ' ')"
        }
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            if (-not (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue)) { break }
            Start-Sleep -Milliseconds 250
        }
        if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
            throw "V3 service '$ServiceName' remained after delete request"
        }
    }
    # A port may belong to an unrelated process. Never kill by port alone.
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) {
        $pids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ','
        throw "Port $Port remains occupied by process(es) $pids; refusing to terminate unrelated listeners"
    }
}

if ($Action -eq 'uninstall') {
    Remove-V3Service
    Write-Host "Research OS V3 service removed. Data preserved at $dataDir"
    exit 0
}

if (-not (Test-Path $serviceExe -PathType Leaf)) {
    throw "V3 ServiceHost executable not found: $serviceExe"
}
if (-not (Test-Path $pythonExe -PathType Leaf)) {
    throw "Bundled Python executable not found: $pythonExe"
}
if (-not (Test-Path (Join-Path $v3Root 'scripts\run_service.py') -PathType Leaf)) {
    throw "V3 service entrypoint not found under $v3Root"
}

New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
Remove-V3Service

$binaryPath = "`"$serviceExe`" --root `"$v3Root`" --python `"$pythonExe`" --port $Port --data-dir `"$dataDir`" --service-name `"$ServiceName`""
New-Service -Name $ServiceName -BinaryPathName $binaryPath -StartupType Automatic -DisplayName 'Research OS V3 Local Service' | Out-Null
Start-Service -Name $ServiceName

$ready = $false
for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
        if ($health.status -eq 'ok') {
            $ready = $true
            break
        }
    }
    catch { }
    Start-Sleep -Milliseconds 500
}

if (-not $ready) {
    throw 'Research OS V3 service did not become ready after installation'
}

$listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop)
if ($listeners.Count -lt 1) {
    throw 'Research OS V3 service has no listening socket after installation'
}
if ($listeners | Where-Object { $_.LocalAddress -ne '127.0.0.1' }) {
    throw 'Research OS V3 service is not loopback-only'
}

Write-Host "Research OS V3 service installed and ready on 127.0.0.1:$Port"
