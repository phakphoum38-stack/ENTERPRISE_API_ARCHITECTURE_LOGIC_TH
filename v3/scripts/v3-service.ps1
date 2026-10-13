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

function Get-V3ServiceRecord {
    $escapedName = $ServiceName.Replace("'", "''")
    return Get-CimInstance Win32_Service -Filter "Name='$escapedName'" -ErrorAction SilentlyContinue
}

function Get-ServiceExecutablePath([string]$CommandLine) {
    $match = [regex]::Match($CommandLine, '^\s*"(?<exe>[^"]+\.exe)"|^\s*(?<exe>.+?\.exe)(?:\s|$)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if (-not $match.Success) {
        throw "Unable to identify executable in service ImagePath: $CommandLine"
    }
    return [System.IO.Path]::GetFullPath($match.Groups['exe'].Value)
}

function Assert-V3ServiceOwnership($ServiceRecord) {
    if (-not $ServiceRecord) { return }
    $expected = [System.IO.Path]::GetFullPath($serviceExe)
    $actual = Get-ServiceExecutablePath ([string]$ServiceRecord.PathName)
    if (-not [string]::Equals($actual, $expected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify service '$ServiceName': ImagePath '$actual' is not the expected Research OS V3 ServiceHost '$expected'"
    }
}

function Test-V3ProcessDescendant([int]$ProcessId, [int]$AncestorProcessId) {
    $current = $ProcessId
    $seen = [System.Collections.Generic.HashSet[int]]::new()
    while ($current -gt 0 -and $seen.Add($current)) {
        if ($current -eq $AncestorProcessId) { return $true }
        $processRecord = Get-CimInstance Win32_Process -Filter "ProcessId = $current" -ErrorAction SilentlyContinue
        if (-not $processRecord) { return $false }
        $current = [int]$processRecord.ParentProcessId
    }
    return $false
}

function Assert-V3OwnedLoopbackListener {
    $serviceRecord = Get-V3ServiceRecord
    if (-not $serviceRecord -or $serviceRecord.State -ne 'Running' -or [int]$serviceRecord.ProcessId -le 0) {
        throw "Research OS V3 service '$ServiceName' is not running with a valid service PID"
    }
    Assert-V3ServiceOwnership $serviceRecord
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop)
    if ($listeners.Count -lt 1) {
        throw "Research OS V3 service has no listening socket on port $Port"
    }
    foreach ($listener in $listeners) {
        if ($listener.LocalAddress -ne '127.0.0.1') {
            throw "V3 listener on port $Port is bound to '$($listener.LocalAddress)', not IPv4 loopback"
        }
        if (-not (Test-V3ProcessDescendant -ProcessId ([int]$listener.OwningProcess) -AncestorProcessId ([int]$serviceRecord.ProcessId))) {
            throw "Port $Port listener PID $($listener.OwningProcess) is not owned by service '$ServiceName' (PID $($serviceRecord.ProcessId)); refusing to trust a foreign /health response"
        }
    }
}

function Remove-V3Service {
    $serviceRecord = Get-V3ServiceRecord
    if ($serviceRecord) {
        Assert-V3ServiceOwnership $serviceRecord
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
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
            if (-not (Get-V3ServiceRecord)) { break }
            Start-Sleep -Milliseconds 250
        }
        if (Get-V3ServiceRecord) {
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

try {
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

    # A successful HTTP response is insufficient: prove the listener belongs to
    # the service process tree, and reject any non-loopback or foreign listener.
    Assert-V3OwnedLoopbackListener
    Write-Host "Research OS V3 service installed and ready on 127.0.0.1:$Port"
}
catch {
    $installFailure = $_.Exception.Message
    try {
        Remove-V3Service
    }
    catch {
        throw "Research OS V3 installation failed: $installFailure. Automatic rollback was incomplete: $($_.Exception.Message)"
    }
    throw "Research OS V3 installation failed and the owned service was rolled back: $installFailure"
}
