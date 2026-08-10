param(
    [ValidateSet('install','uninstall')][string]$Action,
    [string]$Root = "$env:ProgramFiles\Research OS Owner Special",
    [string]$DataDir = "$env:ProgramData\ResearchOSOwnerSpecial",
    [string]$ServiceName = 'ResearchOSOwnerFriendService',
    [string]$OwnerId = 'owner',
    [int]$Port = 8790
)
$ErrorActionPreference = 'Stop'

function Remove-OwnerService {
    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existing) {
        if ($existing.Status -ne 'Stopped') {
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            $existing.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(15))
        }
        sc.exe delete $ServiceName | Out-Host
        for ($i = 0; $i -lt 30; $i++) {
            if (-not (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue)) { break }
            Start-Sleep -Milliseconds 250
        }
    }
}

if ($Action -eq 'uninstall') {
    Remove-OwnerService
    exit 0
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$hostExe = Join-Path $Root 'service_host\ResearchOS.Owner.ServiceHost.exe'
if (-not (Test-Path $hostExe)) { throw "Owner ServiceHost missing: $hostExe" }
Remove-OwnerService
$binary = "`"$hostExe`" --root `"$Root`" --data-dir `"$DataDir`" --owner-id `"$OwnerId`" --port $Port --service-name `"$ServiceName`""
New-Service -Name $ServiceName -BinaryPathName $binary -DisplayName 'Research OS Owner Friend Service' -Description 'Local loopback Friend Runtime for Research OS Owner Special' -StartupType Automatic | Out-Null
Start-Service -Name $ServiceName
(Get-Service -Name $ServiceName).WaitForStatus('Running', [TimeSpan]::FromSeconds(20))
