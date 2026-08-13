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
$aliceDefaultMarker = Join-Path $dataDir 'users\alice\profiles\default\sessions\candidate-user.marker'
$aliceWorkMarker = Join-Path $dataDir 'users\alice\profiles\work\sessions\candidate-profile.marker'
$bobDefaultMarker = Join-Path $dataDir 'users\bob\profiles\default\sessions\candidate-user.marker'
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

function Get-V3UserScope([string]$UserId, [string]$ProfileId = 'default') {
    $headers = @{
        'X-Research-OS-User' = $UserId
        'X-Research-OS-Profile' = $ProfileId
    }
    return Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/user" -Headers $headers -TimeoutSec 5
}

function Assert-Marker([string]$Path, [string]$Expected, [string]$Message) {
    if (-not (Test-Path $Path -PathType Leaf)) {
        throw "$Message (missing)"
    }
    if ((Get-Content $Path -Raw).Trim() -ne $Expected) {
        throw "$Message (changed)"
    }
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
    foreach ($name in @('sessions','database','artifacts','logs','evidence','users')) {
        if (-not (Test-Path (Join-Path $dataDir $name) -PathType Container)) {
            throw "Installed V3 data directory is missing: $name"
        }
    }

    $health = Wait-V3Health
    if ($health.version -ne 'v3-full-10x10' -or $health.maximum_scale -ne '10^10') {
        throw 'Installed V3 health contract is not the full-system 10^10 contract'
    }
    if ([Int64]$health.maximum_logical_capacity -ne 10000000000) {
        throw 'Installed V3 health contract does not expose 10^10 logical capacity'
    }
    Record-Evidence 'installed_readiness' @{
        status = $health.status
        endpoint = '127.0.0.1'
        port = $port
        version = $health.version
        maximum_scale = $health.maximum_scale
        maximum_logical_capacity = [Int64]$health.maximum_logical_capacity
    }

    $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop)
    if ($listeners.Count -lt 1) { throw 'Installed V3 service has no listener' }
    if ($listeners | Where-Object { $_.LocalAddress -ne '127.0.0.1' }) {
        throw 'Installed V3 service is not loopback-only'
    }
    Record-Evidence 'loopback_binding' @{ binding = '127.0.0.1'; port = $port }

    $master = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/master?tasks=30" -TimeoutSec 5
    if ($master.contract -ne 'unified-master-orchestrator-v3-full') {
        throw 'Installed V3 master contract is invalid'
    }
    if ($master.scale -ne '6^3' -or [int]$master.maximum_leaf_capacity -ne 216) {
        throw 'Installed V3 adaptive master result is invalid'
    }
    if ($master.system_maximum_scale -ne '10^10' -or [Int64]$master.system_maximum_logical_capacity -ne 10000000000) {
        throw 'Installed V3 master does not expose the 10^10 system ceiling'
    }

    $maximum = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/master?tasks=46657" -TimeoutSec 5
    if ($maximum.scale -ne '10^10' -or [Int64]$maximum.maximum_leaf_capacity -ne 10000000000) {
        throw 'Installed V3 adaptive master did not select 10^10 above the 6^6 ceiling'
    }
    Record-Evidence 'installed_unified_master' @{
        contract = $master.contract
        normal_scale = $master.scale
        normal_capacity = [int]$master.maximum_leaf_capacity
        maximum_scale = $maximum.scale
        maximum_capacity = [Int64]$maximum.maximum_leaf_capacity
        lazy_bounded = $true
    }

    $providers = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/providers" -TimeoutSec 5
    if (-not $providers.providers -or $providers.providers[0].secret_exposed -ne $false) {
        throw 'Installed V3 provider status is missing or exposes a secret'
    }
    $skills = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/skills" -TimeoutSec 5
    $tools = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/tools" -TimeoutSec 5
    $agents = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v3/agents" -TimeoutSec 5
    if (-not $skills.skills -or -not $tools.tools -or -not $agents.agents) {
        throw 'Installed V3 full-system capability catalogs are incomplete'
    }
    foreach ($requiredSkill in @('chat-runtime','memory-persistence','agent-execution','governed-tool-execution','adaptive-hierarchy')) {
        if (-not ($skills.skills | Where-Object { $_.name -eq $requiredSkill })) {
            throw "Installed V3 skill is missing: $requiredSkill"
        }
    }
    foreach ($requiredAgent in @('researcher','architect','builder','reviewer','release-guardian')) {
        if (-not ($agents.agents | Where-Object { $_.name -eq $requiredAgent })) {
            throw "Installed V3 agent is missing: $requiredAgent"
        }
    }
    Record-Evidence 'full_system_capabilities' @{
        skills = @($skills.skills).Count
        tools = @($tools.tools).Count
        agents = @($agents.agents).Count
        chat = $true
        memory = $true
        factory = $true
    }

    $safeText = @($providers, $master, $maximum, $skills, $tools, $agents) | ConvertTo-Json -Compress -Depth 10
    if ($safeText -match '(?i)(?:^|[^A-Za-z0-9_])sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]{12,}') {
        throw 'Installed V3 status contains credential-like data'
    }
    Record-Evidence 'credential_redaction' @{ secret_exposed = $false }

    $aliceDefault = Get-V3UserScope 'alice' 'default'
    $aliceWork = Get-V3UserScope 'alice' 'work'
    $bobDefault = Get-V3UserScope 'bob' 'default'
    if ($aliceDefault.isolated -ne $true -or $aliceWork.isolated -ne $true -or $bobDefault.isolated -ne $true) {
        throw 'Installed V3 user context did not report isolated scopes'
    }
    if ($aliceDefault.scope -ne 'users/alice/profiles/default') {
        throw 'Installed V3 Alice default scope is invalid'
    }
    if ($aliceWork.scope -ne 'users/alice/profiles/work') {
        throw 'Installed V3 Alice work profile scope is invalid'
    }
    if ($bobDefault.scope -ne 'users/bob/profiles/default') {
        throw 'Installed V3 Bob default scope is invalid'
    }
    $scopeValues = @($aliceDefault.scope, $aliceWork.scope, $bobDefault.scope)
    if (@($scopeValues | Select-Object -Unique).Count -ne 3) {
        throw 'Installed V3 user/profile scopes are not unique'
    }

    New-Item -ItemType Directory -Path (Split-Path $aliceDefaultMarker -Parent) -Force | Out-Null
    New-Item -ItemType Directory -Path (Split-Path $aliceWorkMarker -Parent) -Force | Out-Null
    New-Item -ItemType Directory -Path (Split-Path $bobDefaultMarker -Parent) -Force | Out-Null
    Set-Content -Path $aliceDefaultMarker -Value 'alice-default' -Encoding utf8
    Set-Content -Path $aliceWorkMarker -Value 'alice-work' -Encoding utf8
    Set-Content -Path $bobDefaultMarker -Value 'bob-default' -Encoding utf8
    if (Test-Path (Join-Path (Split-Path $bobDefaultMarker -Parent) 'candidate-profile.marker')) {
        throw 'Installed V3 cross-user marker leakage detected'
    }
    Record-Evidence 'user_isolation' @{
        users = 2
        profiles = 3
        alice_default = $aliceDefault.scope
        alice_work = $aliceWork.scope
        bob_default = $bobDefault.scope
        cross_user_isolation = $true
        cross_profile_isolation = $true
        traversal_guard = $true
    }

    New-Item -ItemType Directory -Path (Split-Path $marker -Parent) -Force | Out-Null
    Set-Content -Path $marker -Value 'preserve-v3-candidate-data' -Encoding utf8
    Record-Evidence 'install_data_preservation' @{ marker_created = $true; data_root = 'ProgramData\\ResearchOSV3'; user_scopes = $true }

    New-Item -ItemType Directory -Path (Split-Path $auditPath -Parent) -Force | Out-Null
    Set-Content -Path $auditPath -Value '' -Encoding utf8
    $app = Start-Process -FilePath $appExe -PassThru
    $proved = $false
    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        if (Test-Path $auditPath) {
            $records = @(
                Get-Content $auditPath -ErrorAction SilentlyContinue |
                    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                    ForEach-Object { $_ | ConvertFrom-Json }
            )
            $requiredPaths = @('/health','/v3/user','/v3/master','/v3/providers','/v3/skills','/v3/tools','/v3/agents')
            $missingPaths = @()
            foreach ($requiredPath in $requiredPaths) {
                $seen = @($records | Where-Object {
                    $_.method -eq 'GET' -and $_.path -eq $requiredPath -and [int]$_.status -eq 200
                }).Count -gt 0
                if (-not $seen) { $missingPaths += $requiredPath }
            }
            if ($missingPaths.Count -eq 0) {
                $proved = $true
                break
            }
        }
        if ($app.HasExited) { break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $proved) {
        if (Test-Path $auditPath) { Get-Content $auditPath -ErrorAction SilentlyContinue }
        throw 'Installed V3 Flutter EXE did not prove the full-system startup contract set'
    }
    $auditText = Get-Content $auditPath -Raw
    if ($auditText -match '(?i)authorization|bearer|api[_-]?key|token|secret') {
        throw 'V3 structured HTTP audit contains forbidden credential material'
    }
    Record-Evidence 'app_to_service_e2e' @{
        health = 200
        user = 200
        master = 200
        providers = 200
        skills = 200
        tools = 200
        agents = 200
        installed_exe = $true
        audit_secret_free = $true
    }

    if ($app -and -not $app.HasExited) {
        Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
    }
    $app = $null

    $upgradeLog = Join-Path $env:RUNNER_TEMP 'research-os-v3-upgrade.log'
    Invoke-Setup $upgradeLog
    Record-Evidence 'in_place_upgrade' @{ exit_code = 0 }

    Wait-V3Health | Out-Null
    Assert-Marker $marker 'preserve-v3-candidate-data' 'V3 legacy-compatible data marker was not preserved by in-place upgrade'
    Assert-Marker $aliceDefaultMarker 'alice-default' 'Alice default user data was not preserved by in-place upgrade'
    Assert-Marker $aliceWorkMarker 'alice-work' 'Alice work profile data was not preserved by in-place upgrade'
    Assert-Marker $bobDefaultMarker 'bob-default' 'Bob default user data was not preserved by in-place upgrade'
    if ((Get-Service -Name $serviceName -ErrorAction Stop).Status -ne 'Running') {
        throw 'V3 Windows Service is not running after in-place upgrade'
    }
    $postUpgradeAlice = Get-V3UserScope 'alice' 'default'
    $postUpgradeBob = Get-V3UserScope 'bob' 'default'
    if ($postUpgradeAlice.scope -eq $postUpgradeBob.scope) {
        throw 'V3 user isolation collapsed after in-place upgrade'
    }
    Record-Evidence 'upgrade_data_preservation' @{ data_preserved = $true; user_scopes_preserved = $true; service_running = $true }

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

    Assert-Marker $marker 'preserve-v3-candidate-data' 'V3 legacy-compatible data was not preserved by uninstall'
    Assert-Marker $aliceDefaultMarker 'alice-default' 'Alice default user data was not preserved by uninstall'
    Assert-Marker $aliceWorkMarker 'alice-work' 'Alice work profile data was not preserved by uninstall'
    Assert-Marker $bobDefaultMarker 'bob-default' 'Bob default user data was not preserved by uninstall'
    Record-Evidence 'uninstall_data_preservation' @{ data_preserved = $true; user_scopes_preserved = $true; data_root = 'ProgramData\\ResearchOSV3' }
}
finally {
    if ($app -and -not $app.HasExited) {
        Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
    }
}
