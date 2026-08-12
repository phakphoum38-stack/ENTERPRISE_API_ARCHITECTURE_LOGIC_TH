param(
    [string]$Root = ".",
    [string]$ReportPath = "file-audit-v6x6-report.json"
)

$ErrorActionPreference = "Stop"

$rootPath = (Resolve-Path $Root).Path
$auditor = Join-Path $rootPath "tools\file_audit_v6x6.py"
if (-not (Test-Path $auditor)) {
    throw "6^6 file audit assistant not found: $auditor"
}

Write-Host "Running Research OS adaptive file audit (logical capacity 6^6 = 46,656)..."
python $auditor $rootPath --json $ReportPath
if ($LASTEXITCODE -ne 0) {
    throw "6^6 file audit failed with exit code $LASTEXITCODE. See $ReportPath"
}

$report = Get-Content $ReportPath -Raw | ConvertFrom-Json
if ($report.contract -ne "adaptive-file-audit-v6x6") {
    throw "Unexpected file-audit contract: $($report.contract)"
}
if ($report.capacity.max_leaf_capacity -ne 46656) {
    throw "6^6 file-audit capacity is invalid: $($report.capacity.max_leaf_capacity)"
}

Write-Host "6^6 file audit passed: $($report.files_scanned) files, $($report.runtime_workers) runtime workers, $($report.errors) errors."
