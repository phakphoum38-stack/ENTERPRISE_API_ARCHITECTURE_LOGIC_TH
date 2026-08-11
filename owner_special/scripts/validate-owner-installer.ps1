param(
    [Parameter(Mandatory=$true)][string]$SetupPath,
    [ValidateSet('full','clean','upgrade','uninstall')][string]$Phase = 'full'
)

$ErrorActionPreference = 'Stop'
$serviceName = 'ResearchOSOwnerFriendService'
$appRoot = Join-Path $env:ProgramFiles 'Research OS Owner Special'
$dataRoot = Join-Path $env:ProgramData 'ResearchOSOwnerSpecial'
$audit = Join-Path $dataRoot 'service\audit.jsonl'
$statePath = Join-Path $env:RUNNER_TEMP 'owner-special-validation-state.json'
$headers = @{'X-Research-OS-Owner'='owner'; 'X-Research-OS-Profile'='default'; 'X-Research-OS-Session'='installer-e2e'}

function Show-OwnerDiagnostics {
    Write-Host '=== Installed Owner Special diagnostics ==='
    $service = Get-Service $serviceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host ((($service | Format-List Name,Status,StartType) | Out-String).Trim())
        sc.exe queryex $serviceName | Out-Host
    } else { Write-Host 'Service is not registered.' }
    foreach ($name in @('service.err.log','service.out.log')) {
        $path = Join-Path $dataRoot "service\logs\$name"
        Write-Host "--- $path ---"
        if (Test-Path $path) { Get-Content $path -Tail 160 | Out-Host } else { Write-Host '<missing>' }
    }
    $python = Join-Path $appRoot 'runtime\python\python.exe'
    if (Test-Path $python) {
        Write-Host "Bundled Python: $python"
        & $python --version 2>&1 | Out-Host
    } else { Write-Host "Bundled Python missing: $python" }
    $entrypoint = Join-Path $appRoot 'owner_special\scripts\run_friend_service.py'
    Write-Host "Friend entrypoint exists: $(Test-Path $entrypoint) ($entrypoint)"
}

function Wait-OwnerReady {
    for ($i=0; $i -lt 80; $i++) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8790/owner/health' -TimeoutSec 2
            if ($health.status -eq 'ok') { return }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    Show-OwnerDiagnostics
    throw 'Installed Owner Friend Service did not become ready'
}

function Get-MemoryPath {
    return (Join-Path $dataRoot 'owners\owner\memory\memory.json')
}

function Read-ValidationState {
    if (-not (Test-Path $statePath)) {
        throw "Owner validation state missing: $statePath"
    }
    return (Get-Content $statePath -Raw | ConvertFrom-Json)
}

function Write-ValidationState([hashtable]$State) {
    $State | ConvertTo-Json -Depth 6 | Set-Content $statePath -Encoding utf8
}

function Invoke-CleanValidation {
    Write-Host '=== PHASE: CLEAN INSTALL ==='
    if (Get-Service $serviceName -ErrorAction SilentlyContinue) {
        & "$PSScriptRoot\install-owner-service.ps1" -Action uninstall -Root $appRoot -DataDir $dataRoot
    }
    if (Test-Path $appRoot) { Remove-Item $appRoot -Recurse -Force }
    if (Test-Path $dataRoot) { Remove-Item $dataRoot -Recurse -Force }
    if (Test-Path $statePath) { Remove-Item $statePath -Force }

    $env:RESEARCH_OS_MOCK_PROVIDER_KEY = 'ci-owner-provider-key'
    $mock = Start-Process -FilePath python -ArgumentList @('owner_special/scripts/mock_openai_provider.py','--port','18991') -PassThru
    try {
        Start-Sleep -Seconds 1
        $setupLog = Join-Path $env:RUNNER_TEMP 'owner-special-setup.log'
        $install = Start-Process -FilePath $SetupPath -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/LOG=$setupLog") -Wait -PassThru
        Write-Host "Owner clean installer exit code: $($install.ExitCode)"
        if ($install.ExitCode -ne 0) {
            if (Test-Path $setupLog) { Get-Content $setupLog -Tail 160 | Out-Host }
            throw "Owner clean installer failed: exit code $($install.ExitCode)"
        }
        Wait-OwnerReady

        $service = Get-Service $serviceName -ErrorAction Stop
        if ($service.Status -ne 'Running') { throw 'Owner Windows Service is not running after clean install' }
        $unsafe = @(Get-NetTCPConnection -LocalPort 8790 -State Listen | Where-Object { $_.LocalAddress -notin @('127.0.0.1','::1') })
        if ($unsafe) { throw 'Owner Friend Service must be loopback-only' }

        $status = Invoke-RestMethod -Uri 'http://127.0.0.1:8790/owner/status' -Headers $headers -TimeoutSec 5
        if ([int]$status.brain_profiles.'fast-1m' -ne 1000000) { throw 'fast-1m capacity missing after install' }
        if ([int]$status.helper_scheduler.max_active_workers -gt 128) { throw 'active worker cap is unsafe' }

        $providerBody = @{base_url='http://127.0.0.1:18991/v1'; model='mock-model'; api_key='ci-owner-provider-key'; enabled=$true} | ConvertTo-Json
        $provider = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8790/owner/provider/config' -Headers $headers -ContentType 'application/json' -Body $providerBody -TimeoutSec 10
        if (-not $provider.credential_present -or $provider.secret_exposed) { throw 'Provider secret boundary failed' }
        $serialized = $provider | ConvertTo-Json -Compress
        if ($serialized -match 'ci-owner-provider-key') { throw 'Provider status exposed credential' }
        $providerTest = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8790/owner/provider/test' -Headers $headers -ContentType 'application/json' -Body '{"test":true}' -TimeoutSec 10
        if (-not $providerTest.connected) { throw 'Installed OpenAI-compatible provider test failed' }

        $chatBody = @{text='installer turbo test'; complexity=9; risk=7; parallelism=128; helper_budget=1000000; requested_skills=@('analysis','planning','quality')} | ConvertTo-Json
        $chat = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8790/owner/chat' -Headers $headers -ContentType 'application/json' -Body $chatBody -TimeoutSec 20
        if ($chat.decision.scale -ne 'fast-1m' -or [int]$chat.decision.capacity -ne 1000000) { throw 'Turbo 1M decision failed' }
        if ([int]$chat.helpers.active_workers -gt 128 -or [int]$chat.helpers.planned_helpers -ne 1000000) { throw 'Bounded helper scheduler failed' }
        if ($chat.provider -ne 'openai-compatible' -or $chat.text -notmatch '^mock-provider:') { throw 'Real provider routing path failed' }

        $memoryPath = Get-MemoryPath
        if (-not (Test-Path $memoryPath)) { throw 'Owner memory was not persisted' }
        $beforeUpgrade = (Get-FileHash $memoryPath -Algorithm SHA256).Hash

        if (Test-Path $audit) { Clear-Content $audit -ErrorAction SilentlyContinue }
        $appExe = Join-Path $appRoot 'app\research_os_owner_special.exe'
        if (-not (Test-Path $appExe)) { throw 'Installed Owner Desktop EXE missing' }
        $app = Start-Process $appExe -PassThru
        try {
            $proved = $false
            for ($i=0; $i -lt 60; $i++) {
                if ($app.HasExited) { throw 'Owner Desktop exited before startup E2E proof' }
                if (Test-Path $audit) {
                    $records = @(Get-Content $audit -ErrorAction SilentlyContinue | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
                    $healthSeen = @($records | Where-Object { $_.path -eq '/owner/health' -and [int]$_.status -eq 200 }).Count -gt 0
                    $statusSeen = @($records | Where-Object { $_.path -eq '/owner/status' -and [int]$_.status -eq 200 }).Count -gt 0
                    $providerSeen = @($records | Where-Object { $_.path -eq '/owner/provider' -and [int]$_.status -eq 200 }).Count -gt 0
                    if ($healthSeen -and $statusSeen -and $providerSeen) { $proved = $true; break }
                }
                Start-Sleep -Milliseconds 300
            }
            if (-not $proved) { throw 'Installed Owner Desktop did not prove health/status/provider startup requests' }
        } finally {
            if (-not $app.HasExited) { Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue }
        }

        $setupHash = (Get-FileHash $SetupPath -Algorithm SHA256).Hash.ToLowerInvariant()
        Write-ValidationState @{
            clean_install = 'passed'
            setup_sha256 = $setupHash
            memory_sha256_before_upgrade = $beforeUpgrade
            provider_connected = $true
            helper_logical_capacity = 1000000
            max_active_workers = 128
        }
        Write-Host 'CLEAN INSTALL VALIDATION PASSED'
    } catch {
        Show-OwnerDiagnostics
        throw
    } finally {
        if ($mock -and -not $mock.HasExited) { Stop-Process -Id $mock.Id -Force -ErrorAction SilentlyContinue }
    }
}

function Invoke-UpgradeValidation {
    Write-Host '=== PHASE: IN-PLACE UPGRADE ==='
    try {
        $state = Read-ValidationState
        $memoryPath = Get-MemoryPath
        if (-not (Test-Path $memoryPath)) { throw 'Owner memory missing before upgrade' }
        $currentBefore = (Get-FileHash $memoryPath -Algorithm SHA256).Hash
        if ($currentBefore -ne [string]$state.memory_sha256_before_upgrade) { throw 'Owner memory changed before upgrade phase started' }

        # Quiesce the running service and bundled Python before in-place upgrade so that
        # the installer's PrepareToInstall check does not time out waiting for python.exe
        # to release file handles (which causes exit code 7 / Access denied on file replacement).
        Write-Host 'Quiescing Owner Friend Service and bundled Python before upgrade.'
        $svc = Get-Service $serviceName -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -ne 'Stopped') {
            Stop-Service $serviceName -Force -ErrorAction SilentlyContinue
            $svc.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(20))
        }
        $bundledPython = Join-Path $appRoot 'runtime\python\python.exe'
        $resolved = if (Test-Path $bundledPython) { [IO.Path]::GetFullPath($bundledPython) } else { $null }
        if ($resolved) {
            for ($i = 0; $i -lt 20; $i++) {
                $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
                    Where-Object { $_.ExecutablePath -and ([IO.Path]::GetFullPath($_.ExecutablePath) -ieq $resolved) })
                if ($procs.Count -eq 0) { break }
                Start-Sleep -Milliseconds 500
            }
            Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
                Where-Object { $_.ExecutablePath -and ([IO.Path]::GetFullPath($_.ExecutablePath) -ieq $resolved) } |
                ForEach-Object {
                    Write-Host "Forcibly stopping lingering bundled python.exe PID $($_.ProcessId)."
                    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                }
            Start-Sleep -Milliseconds 500
        }
        Write-Host 'Owner Friend Service and bundled Python quiesced; proceeding with upgrade installer.'

        $upgradeLog = Join-Path $env:RUNNER_TEMP 'owner-special-upgrade.log'
        $upgrade = Start-Process -FilePath $SetupPath -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/LOG=$upgradeLog") -Wait -PassThru
        Write-Host "Owner in-place upgrade installer exit code: $($upgrade.ExitCode)"
        if ($upgrade.ExitCode -ne 0) {
            if (Test-Path $upgradeLog) { Get-Content $upgradeLog -Tail 160 | Out-Host }
            throw "Owner in-place upgrade failed: exit code $($upgrade.ExitCode)"
        }
        Wait-OwnerReady
        if (-not (Test-Path $memoryPath)) { throw 'Owner memory missing after upgrade' }
        $afterUpgrade = (Get-FileHash $memoryPath -Algorithm SHA256).Hash
        if ([string]$state.memory_sha256_before_upgrade -ne $afterUpgrade) { throw 'Owner memory changed unexpectedly during upgrade' }

        Write-ValidationState @{
            clean_install = 'passed'
            upgrade = 'passed'
            setup_sha256 = [string]$state.setup_sha256
            memory_sha256_before_upgrade = [string]$state.memory_sha256_before_upgrade
            memory_sha256_after_upgrade = $afterUpgrade
            provider_connected = [bool]$state.provider_connected
            helper_logical_capacity = [int]$state.helper_logical_capacity
            max_active_workers = [int]$state.max_active_workers
        }
        Write-Host 'IN-PLACE UPGRADE VALIDATION PASSED'
    } catch {
        Show-OwnerDiagnostics
        throw
    }
}

function Invoke-UninstallValidation {
    Write-Host '=== PHASE: UNINSTALL + DATA PRESERVATION ==='
    try {
        $state = Read-ValidationState
        if ([string]$state.upgrade -ne 'passed') { throw 'Upgrade validation state is not passed' }
        $memoryPath = Get-MemoryPath
        if (-not (Test-Path $memoryPath)) { throw 'Owner memory missing before uninstall' }

        $uninstaller = Get-ChildItem $appRoot -Filter 'unins*.exe' -File | Select-Object -First 1
        if (-not $uninstaller) { throw 'Owner uninstaller missing' }
        $uninstall = Start-Process $uninstaller.FullName -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
        Write-Host "Owner uninstaller exit code: $($uninstall.ExitCode)"
        if ($uninstall.ExitCode -ne 0) { throw "Owner uninstall failed: exit code $($uninstall.ExitCode)" }
        Start-Sleep -Seconds 2
        if (Get-Service $serviceName -ErrorAction SilentlyContinue) { throw 'Owner Windows Service remained after uninstall' }
        if (-not (Test-Path $memoryPath)) { throw 'Owner data was not preserved after uninstall' }
        $afterUninstall = (Get-FileHash $memoryPath -Algorithm SHA256).Hash
        if ($afterUninstall -ne [string]$state.memory_sha256_after_upgrade) { throw 'Owner memory changed unexpectedly during uninstall' }

        $evidenceDir = Join-Path $PSScriptRoot '..\installer\output'
        New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
        @{
            validation = 'passed'
            clean_install = 'passed'
            upgrade = 'passed'
            uninstall = 'passed'
            setup_sha256 = [string]$state.setup_sha256
            helper_logical_capacity = [int]$state.helper_logical_capacity
            max_active_workers = [int]$state.max_active_workers
            provider = 'openai-compatible'
            provider_connected = [bool]$state.provider_connected
            memory_preserved = $true
            service_name = $serviceName
        } | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $evidenceDir 'owner-v1.3-validation.json') -Encoding utf8
        Write-Host 'UNINSTALL + DATA PRESERVATION VALIDATION PASSED'
    } catch {
        Show-OwnerDiagnostics
        throw
    }
}

switch ($Phase) {
    'clean' { Invoke-CleanValidation }
    'upgrade' { Invoke-UpgradeValidation }
    'uninstall' { Invoke-UninstallValidation }
    'full' {
        Invoke-CleanValidation
        Invoke-UpgradeValidation
        Invoke-UninstallValidation
    }
}
