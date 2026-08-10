param([Parameter(Mandatory=$true)][string]$SetupPath)
$ErrorActionPreference = 'Stop'
$serviceName = 'ResearchOSOwnerFriendService'
$appRoot = Join-Path $env:ProgramFiles 'Research OS Owner Special'
$dataRoot = Join-Path $env:ProgramData 'ResearchOSOwnerSpecial'
$audit = Join-Path $dataRoot 'service\audit.jsonl'
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

if (Get-Service $serviceName -ErrorAction SilentlyContinue) { & "$PSScriptRoot\install-owner-service.ps1" -Action uninstall -Root $appRoot -DataDir $dataRoot }
if (Test-Path $appRoot) { Remove-Item $appRoot -Recurse -Force }
if (Test-Path $dataRoot) { Remove-Item $dataRoot -Recurse -Force }

$env:RESEARCH_OS_MOCK_PROVIDER_KEY = 'ci-owner-provider-key'
$mock = Start-Process -FilePath python -ArgumentList @('owner_special/scripts/mock_openai_provider.py','--port','18991') -PassThru
try {
    Start-Sleep -Seconds 1
    $setupLog = Join-Path $env:RUNNER_TEMP 'owner-special-setup.log'
    $install = Start-Process -FilePath $SetupPath -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/LOG=$setupLog") -Wait -PassThru
    if ($install.ExitCode -ne 0) {
        if (Test-Path $setupLog) { Get-Content $setupLog -Tail 160 | Out-Host }
        throw "Owner installer failed: $($install.ExitCode)"
    }
    Wait-OwnerReady

    $service = Get-Service $serviceName -ErrorAction Stop
    if ($service.Status -ne 'Running') { throw 'Owner Windows Service is not running' }
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

    $memoryPath = Join-Path $dataRoot 'owners\owner\memory\memory.json'
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
    } finally { if (-not $app.HasExited) { Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue } }

    $upgradeLog = Join-Path $env:RUNNER_TEMP 'owner-special-upgrade.log'
    $upgrade = Start-Process -FilePath $SetupPath -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/LOG=$upgradeLog") -Wait -PassThru
    if ($upgrade.ExitCode -ne 0) {
        if (Test-Path $upgradeLog) { Get-Content $upgradeLog -Tail 160 | Out-Host }
        throw 'Owner in-place upgrade failed'
    }
    Wait-OwnerReady
    if (-not (Test-Path $memoryPath)) { throw 'Owner memory missing after upgrade' }
    $afterUpgrade = (Get-FileHash $memoryPath -Algorithm SHA256).Hash
    if ($beforeUpgrade -ne $afterUpgrade) { throw 'Owner memory changed unexpectedly during upgrade' }

    $uninstaller = Get-ChildItem $appRoot -Filter 'unins*.exe' -File | Select-Object -First 1
    if (-not $uninstaller) { throw 'Owner uninstaller missing' }
    $uninstall = Start-Process $uninstaller.FullName -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
    if ($uninstall.ExitCode -ne 0) { throw 'Owner uninstall failed' }
    Start-Sleep -Seconds 2
    if (Get-Service $serviceName -ErrorAction SilentlyContinue) { throw 'Owner Windows Service remained after uninstall' }
    if (-not (Test-Path $memoryPath)) { throw 'Owner data was not preserved after uninstall' }

    $evidenceDir = Join-Path $PSScriptRoot '..\installer\output'
    New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
    $setupHash = (Get-FileHash $SetupPath -Algorithm SHA256).Hash.ToLowerInvariant()
    @{validation='passed'; setup_sha256=$setupHash; helper_logical_capacity=1000000; max_active_workers=128; provider='openai-compatible'; provider_connected=$true; memory_preserved=$true; service_name=$serviceName} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $evidenceDir 'owner-v1.3-validation.json') -Encoding utf8
} catch {
    Show-OwnerDiagnostics
    throw
} finally {
    if ($mock -and -not $mock.HasExited) { Stop-Process -Id $mock.Id -Force -ErrorAction SilentlyContinue }
}
