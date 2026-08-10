param(
    [Parameter(Mandatory = $true)]
    [string]$SetupPath,

    [Parameter(Mandatory = $true)]
    [string]$EvidencePath
)

$ErrorActionPreference = 'Stop'

$v3Root = Split-Path -Parent $PSScriptRoot
$evidenceScript = Join-Path $v3Root 'scripts\evidence.py'
$setup = (Resolve-Path $SetupPath).Path
$evidence = [System.IO.Path]::GetFullPath($EvidencePath)
$installDir = Join-Path $env:ProgramFiles 'Research OS V3'
$dataDir = Join-Path $env:ProgramData 'ResearchOSV3'
$serviceName = 'ResearchOSV3Service'
$port = 8788
$appExe = Join-Path $installDir 'app\research_os_v3_flutter.exe'
$auditPath = Join-Path $dataDir 'logs\http-audit.jsonl'
$marker = Join-Path $dataDir 'sessions\candidate-preservation.marker'
$app = $null

function Record-Evidence([string]$Stage, [hashtable]$Data = @{}) {
    $json = $Data | ConvertTo-Json -Compress -Depth 10
    & python $evidenceScript --output $evidence --stage $Stage --status passed --data $json
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to record candidate evidence for $Stage"
    }
}

function Wait-V3Health {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
            if ($health.status -eq 'ok') {
                return $health
            }
        }
        catch { }
        Start-Sleep -Milliseconds 500
    }
    throw 'Research OS V3 local service did not become ready'
}

function Invoke-Setup([string]$LogPath) {
    $process = Start-Process -FilePath $setup `
        -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/LOG=$LogPath") `
        -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Research OS V3 Setup failed with exit code $($process.ExitCode)"
    }
}

function Remove-StaleInstallation {
    $uninstaller = Get-ChildItem $installDir -Filter 'unins*.exe' -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($uninstaller) {
        Start-Process -FilePath $uninstaller.FullName -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait | Out-Null
    }

    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($service -and $service.Status -ne 'Stopped') {
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    }
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
        sc.exe delete $serviceName | Out-Null
        Start-Sleep -Seconds 1
    }

    $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    foreach ($listener in $listeners) {
        Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $installDir) {
        Remove-Item $installDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

try {
    Remove-StaleInstallation
    if (Test-Path $dataDir) {
        Remove-Item $dataDir -Recurse -Force
    }

    $installLog = Join-Path $env:RUNNER_TEMP 'research-os-v3-install.log'
    Invoke-Setup $installLog
    Record-Evidence 'install' @{ exit_code = 0; mode = 'clean' }

    if (-not (Test-Path $appExe -PathType Leaf)) {
        throw "Installed V3 Flutter executable is missing: $appExe"
    }
    foreach ($name in @('sessions','database','artifacts','logs','evidence')) {
        if (-not (Test-Path (Join-Path $dataDir $name) -PathType Container)) {
            throw "Installed V3 data directory is missing: $name"
        }
    }

    $health = Wait-V3Health
    Record-Evidence 'installed_readiness' @{ status = $health.status; endpoint = '127.0.0.1'; port = $port }

    $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop)
    if ($listeners.Count -lt 1) { throw 'Installed V3 service has no listener' }
    if ($listeners | Where-Object { $_.LocalAddress -ne '127.0.0.1' }) {
        throw 'Installed V3 service is not loopback-only'
    }
    Record-Evidence 'loopback_binding' @{ binding = '127.0.0.1'; port = $port }

    $master = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/master?tasks=30" -TimeoutSec 5
    if ($master.contract -ne 'unified-master-orchestrator-v3-clean') {
        throw 'Installed V3 master contract is invalid'
    }
    if ($master.scale -ne '6^3' -or [int]$master.maximum_leaf_capacity -ne 216) {
        throw 'Installed V3 adaptive master result is invalid'
    }
    Record-Evidence 'installed_unified_master' @{
        contract = $master.contract
        scale = $master.scale
        capacity = [int]$master.maximum_leaf_capacity
    }

    $providers = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/providers" -TimeoutSec 5
    if (-not $providers.providers -or $providers.providers[0].secret_exposed -ne $false) {
        throw 'Installed V3 provider status is missing or exposes a secret'
    }
    $safeText = @($providers, $master) | ConvertTo-Json -Compress -Depth 10
    if ($safeText -match '(?i)(?:^|[^A-Za-z0-9_])sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]{12,}') {
        throw 'Installed V3 status contains credential-like data'
    }
    Record-Evidence 'credential_redaction' @{ secret_exposed = $false }

    New-Item -ItemType Directory -Path (Split-Path $marker -Parent) -Force | Out-Null
    Set-Content -Path $marker -Value 'preserve-v3-candidate-data' -Encoding utf8
    Record-Evidence 'install_data_preservation' @{ marker_created = $true; data_root = 'ProgramData\\ResearchOSV3' }

    New-Item -ItemType Directory -Path (Split-Path $auditPath -Parent) -Force | Out-Null
    Set-Content -Path $auditPath -Value '' -Encoding utf8
    $app = Start-Process -FilePath $appExe -PassThru
    $proved = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if (Test-Path $auditPath) {
            $records = @(
                Get-Content $auditPath -ErrorAction SilentlyContinue |
                    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                    ForEach-Object { $_ | ConvertFrom-Json }
            )
            $healthSeen = @($records | Where-Object {
                $_.method -eq 'GET' -and $_.path -eq '/health' -and [int]$_.status -eq 200
            }).Count -gt 0
            $providersSeen = @($records | Where-Object {
                $_.method -eq 'GET' -and $_.path -eq '/v3/providers' -and [int]$_.status -eq 200
            }).Count -gt 0
            if ($healthSeen -and $providersSeen) {
                $proved = $true
                break
            }
        }
        if ($app.HasExited) { break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $proved) {
        if (Test-Path $auditPath) { Get-Content $auditPath -ErrorAction SilentlyContinue }
        throw 'Installed V3 Flutter EXE did not prove /health and /v3/providers requests'
    }
    $auditText = Get-Content $auditPath -Raw
    if ($auditText -match '(?i)authorization|bearer|api[_-]?key|token|secret') {
        throw 'V3 structured HTTP audit contains forbidden credential material'
    }
    Record-Evidence 'app_to_service_e2e' @{ health = 200; providers = 200; installed_exe = $true; audit_secret_free = $true }

    if ($app -and -not $app.HasExited) {
        Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
    }
    $app = $null

    $upgradeLog = Join-Path $env:RUNNER_TEMP 'research-os-v3-upgrade.log'
    Invoke-Setup $upgradeLog
    Record-Evidence 'in_place_upgrade' @{ exit_code = 0 }

    Wait-V3Health | Out-Null
    if (-not (Test-Path $marker -PathType Leaf)) {
        throw 'V3 data marker was removed by in-place upgrade'
    }
    if ((Get-Content $marker -Raw).Trim() -ne 'preserve-v3-candidate-data') {
        throw 'V3 data marker changed during in-place upgrade'
    }
    if ((Get-Service -Name $serviceName -ErrorAction Stop).Status -ne 'Running') {
        throw 'V3 Windows Service is not running after in-place upgrade'
    }
    Record-Evidence 'upgrade_data_preservation' @{ data_preserved = $true; service_running = $true }

    $uninstaller = Get-ChildItem $installDir -Filter 'unins*.exe' -File -ErrorAction Stop |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $uninstaller) { throw 'Research OS V3 uninstaller was not found' }
    $uninstall = Start-Process -FilePath $uninstaller.FullName `
        -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') `
        -Wait -PassThru
    if ($uninstall.ExitCode -ne 0) {
        throw "Research OS V3 uninstall failed with exit code $($uninstall.ExitCode)"
    }

    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if (-not (Get-Service -Name $serviceName -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Milliseconds 250
    }
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
        throw 'V3 Windows Service remained after uninstall'
    }
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw 'V3 listener remained after uninstall'
    }
    if (Test-Path $appExe -PathType Leaf) {
        throw 'V3 Flutter executable remained after uninstall'
    }
    Record-Evidence 'uninstall' @{ exit_code = 0; service_removed = $true; listener_removed = $true; app_removed = $true }

    if (-not (Test-Path $marker -PathType Leaf)) {
        throw 'V3 user data was removed by uninstall'
    }
    if ((Get-Content $marker -Raw).Trim() -ne 'preserve-v3-candidate-data') {
        throw 'V3 preserved user data changed during uninstall'
    }
    Record-Evidence 'uninstall_data_preservation' @{ data_preserved = $true; data_root = 'ProgramData\\ResearchOSV3' }
}
finally {
    if ($app -and -not $app.HasExited) {
        Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
    }
}
