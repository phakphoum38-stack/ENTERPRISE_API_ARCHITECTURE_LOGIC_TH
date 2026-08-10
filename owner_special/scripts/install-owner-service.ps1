param(
    [ValidateSet('install','uninstall')][string]$Action,
    [string]$Root = "$env:ProgramFiles\Research OS Owner Special",
    [string]$DataDir = "$env:ProgramData\ResearchOSOwnerSpecial",
    [string]$ServiceName = 'ResearchOSOwnerFriendService',
    [string]$OwnerId = 'owner',
    [int]$Port = 8790
)
$ErrorActionPreference = 'Stop'

function Show-OwnerServiceDiagnostics {
    Write-Host '--- Owner Friend service diagnostics ---'
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host ((($service | Format-List Name,Status,StartType) | Out-String).Trim())
        sc.exe queryex $ServiceName | Out-Host
    } else {
        Write-Host 'Service is not registered.'
    }
    foreach ($name in @('service.err.log','service.out.log')) {
        $path = Join-Path $DataDir "service\logs\$name"
        Write-Host "--- $path ---"
        if (Test-Path $path) { Get-Content $path -Tail 120 | Out-Host } else { Write-Host '<missing>' }
    }
}

function Remove-OwnerService {
    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existing) {
        if ($existing.Status -ne 'Stopped') {
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            try { $existing.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(20)) } catch {}
        }
        sc.exe delete $ServiceName | Out-Null
        for ($i = 0; $i -lt 40; $i++) {
            if (-not (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue)) { break }
            Start-Sleep -Milliseconds 250
        }
    }
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    foreach ($listener in $listeners) { Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue }
}

if ($Action -eq 'uninstall') {
    Remove-OwnerService
    Write-Host "Owner Friend service removed. Owner data preserved at $DataDir"
    exit 0
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$hostExe = Join-Path $Root 'service_host\ResearchOS.Owner.ServiceHost.exe'
$pythonExe = Join-Path $Root 'runtime\python\python.exe'
$entrypoint = Join-Path $Root 'owner_special\scripts\run_friend_service.py'
foreach ($required in @($hostExe,$pythonExe,$entrypoint)) {
    if (-not (Test-Path $required -PathType Leaf)) { throw "Owner service package file missing: $required" }
}

Remove-OwnerService
$binary = "`"$hostExe`" --root `"$Root`" --python `"$pythonExe`" --data-dir `"$DataDir`" --owner-id `"$OwnerId`" --port $Port --service-name `"$ServiceName`""
New-Service -Name $ServiceName -BinaryPathName $binary -DisplayName 'Research OS Owner Friend Service' -Description 'Local loopback Friend Runtime for Research OS Owner Special' -StartupType Automatic | Out-Null
Start-Service -Name $ServiceName

$ready = $false
for ($i = 0; $i -lt 80; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/owner/health" -TimeoutSec 2
        if ($health.status -eq 'ok') { $ready = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $ready) {
    Show-OwnerServiceDiagnostics
    throw 'Owner Friend Windows Service did not become HTTP-ready after installation'
}

$listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop)
if ($listeners.Count -lt 1) { throw 'Owner Friend service has no listening socket after installation' }
if ($listeners | Where-Object { $_.LocalAddress -notin @('127.0.0.1','::1') }) { throw 'Owner Friend service is not loopback-only' }
Write-Host "Owner Friend service installed and ready on 127.0.0.1:$Port"
