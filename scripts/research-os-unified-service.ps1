param(
    [ValidateSet('install','uninstall','start','stop','restart','status')]
    [string]$Action = 'status',
    [string]$DataDir = "$env:ProgramData\ResearchOS",
    [string]$ServiceName = 'ResearchOSService'
)

$ErrorActionPreference = 'Stop'
$BaseScript = Join-Path $PSScriptRoot 'research-os-service.ps1'
if (-not (Test-Path $BaseScript -PathType Leaf)) {
    throw "Base Research OS service script missing: $BaseScript"
}

function Set-LoopbackEnvironment {
    $serviceKey = "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName"
    if (-not (Test-Path $serviceKey)) {
        throw "Research OS service registry key missing: $serviceKey"
    }

    $values = @((Get-ItemProperty -Path $serviceKey -Name Environment -ErrorAction Stop).Environment)
    $updated = @()
    $foundHost = $false
    foreach ($value in $values) {
        if ([string]$value -like 'RESEARCH_OS_API_HOST=*') {
            $updated += 'RESEARCH_OS_API_HOST=127.0.0.1'
            $foundHost = $true
        } else {
            $updated += [string]$value
        }
    }
    if (-not $foundHost) {
        $updated += 'RESEARCH_OS_API_HOST=127.0.0.1'
    }
    New-ItemProperty -Path $serviceKey -Name Environment -PropertyType MultiString -Value $updated -Force | Out-Null
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_API_HOST', '127.0.0.1', 'Machine')
}

function Wait-LoopbackReady([int]$Port = 8787, [int]$Seconds = 40) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
            if ($health.status -eq 'ok') {
                $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop)
                if ($listeners.Count -gt 0 -and -not ($listeners | Where-Object { $_.LocalAddress -notin @('127.0.0.1','::1') })) {
                    return
                }
            }
        } catch {}
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "Research OS API did not become loopback-ready on 127.0.0.1:$Port"
}

if ($Action -ne 'install') {
    & $BaseScript -Action $Action -DataDir $DataDir -ServiceName $ServiceName
    exit $LASTEXITCODE
}

& $BaseScript -Action install -DataDir $DataDir -ServiceName $ServiceName
if ($LASTEXITCODE -ne 0) {
    throw "Base Research OS service install failed with exit code $LASTEXITCODE"
}

Stop-Service -Name $ServiceName -Force -ErrorAction Stop
(Get-Service -Name $ServiceName -ErrorAction Stop).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(20))
Set-LoopbackEnvironment
Start-Service -Name $ServiceName
(Get-Service -Name $ServiceName -ErrorAction Stop).WaitForStatus('Running', [TimeSpan]::FromSeconds(20))
Wait-LoopbackReady
Write-Host 'Research OS unified service is ready on loopback 127.0.0.1:8787.'
