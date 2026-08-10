param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [Parameter(Mandatory = $true)]
    [string]$Stage,

    [ValidateSet('started', 'passed', 'failed', 'skipped')]
    [string]$Status = 'passed',

    [string]$DataJson = '{}'
)

$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$progressPath = Join-Path $OutputDir 'progress.json'
$now = [DateTimeOffset]::UtcNow.ToString('o')

if (Test-Path $progressPath) {
    $progress = Get-Content $progressPath -Raw | ConvertFrom-Json -AsHashtable
}
else {
    $progress = [ordered]@{
        schema_version = 1
        target_sha = $env:TARGET_SHA
        candidate_run = $env:GITHUB_RUN_ID
        started_at = $now
        updated_at = $now
        stages = [ordered]@{}
    }
}

if ($null -eq $progress['stages']) {
    $progress['stages'] = [ordered]@{}
}

$entry = [ordered]@{
    status = $Status
    recorded_at = $now
}

if (-not [string]::IsNullOrWhiteSpace($DataJson)) {
    $data = $DataJson | ConvertFrom-Json -AsHashtable
    foreach ($key in $data.Keys) {
        $entry[$key] = $data[$key]
    }
}

$progress['target_sha'] = $env:TARGET_SHA
$progress['candidate_run'] = $env:GITHUB_RUN_ID
$progress['updated_at'] = $now
$progress['stages'][$Stage] = $entry

$tmpPath = "$progressPath.tmp"
$progress | ConvertTo-Json -Depth 20 | Set-Content $tmpPath -Encoding utf8
Move-Item -Path $tmpPath -Destination $progressPath -Force

Write-Host "Recorded candidate evidence: $Stage = $Status"
