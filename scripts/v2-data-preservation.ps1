param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('Seed','Verify')]
  [string]$Action,

  [string]$DataDir = "$env:ProgramData\ResearchOS",

  [string]$ManifestPath = "$env:RUNNER_TEMP\research-os-v1-data-fixture.json"
)

$ErrorActionPreference = 'Stop'

$fixtures = [ordered]@{
  'database\v1-memory.db.fixture' = 'v1-memory-database-preserve'
  'sessions\v1-session.json' = '{"version":"1.0.0","preserve":true}'
  'artifacts\v1-artifact.md' = '# V1 Artifact`nPreserve across V2 upgrade.'
  'backups\v1-backup.fixture' = 'v1-backup-preserve'
  'logs\v1-history.log' = 'v1-log-preserve'
}

function Get-Sha256([string]$Path) {
  return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ($Action -eq 'Seed') {
  New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
  $entries = @()
  foreach ($relative in $fixtures.Keys) {
    $path = Join-Path $DataDir $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $path -Parent) | Out-Null
    Set-Content -Path $path -Value $fixtures[$relative] -Encoding UTF8 -NoNewline
    $entries += [ordered]@{
      relative_path = $relative
      sha256 = Get-Sha256 $path
      size_bytes = (Get-Item $path).Length
    }
  }
  $manifest = [ordered]@{
    schema_version = 1
    source_version = '1.0.0'
    target_family = '2.x'
    data_dir = $DataDir
    entries = $entries
  }
  $manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $ManifestPath -Encoding UTF8
  Write-Host "Seeded V1 data preservation fixture: $ManifestPath"
  exit 0
}

if (-not (Test-Path $ManifestPath)) {
  throw "Fixture manifest missing: $ManifestPath"
}
$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
foreach ($entry in $manifest.entries) {
  $path = Join-Path $DataDir $entry.relative_path
  if (-not (Test-Path $path)) {
    throw "Preserved V1 data file missing: $path"
  }
  $actual = Get-Sha256 $path
  if ($actual -ne $entry.sha256) {
    throw "Preserved V1 data changed: $($entry.relative_path) expected=$($entry.sha256) actual=$actual"
  }
}
Write-Host "V1 local data fixture preserved across installer operation."
