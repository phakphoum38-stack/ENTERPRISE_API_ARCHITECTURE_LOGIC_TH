param(
  [Parameter(Mandatory=$true)]
  [string]$DriveRoot
)

$ErrorActionPreference = 'Stop'

$ProgramRoot = 'C:\Program Files\Research OS\cloud'
$StateRoot = 'C:\ProgramData\ResearchOS\cloud'
$LegacyStateRoot = 'C:\ProgramData\DriveVirtualCloud'
$WorkerRoot = Join-Path $ProgramRoot 'worker'
$RootId = '1FqR9bfxgaSNL99jmSR9hRPdmkhFyKlEY'
$Owner = 'phakphoum38-stack'
$TaskName = 'ResearchOSDriveCloudMirrorWorker'
$LegacyTaskName = 'DriveVirtualCloudMirrorWorker'

if (-not (Test-Path -LiteralPath $DriveRoot)) {
  throw "Drive root not found: $DriveRoot"
}

$requiredDriveFolders = @(
  'runtime\state',
  'runtime\manifests',
  'github\mirrors\bare',
  'github\bundles\full',
  'github\bundles\incremental',
  'github\sync\state',
  'github\sync\checkpoints',
  'github\restore\incoming',
  'github\restore\verified',
  'github\restore\completed',
  'github\restore\failed',
  'backup\snapshots',
  'backup\restore_points',
  'logs\github'
)
foreach ($relative in $requiredDriveFolders) {
  New-Item -ItemType Directory -Force -Path (Join-Path $DriveRoot $relative) | Out-Null
}

New-Item -ItemType Directory -Force -Path $ProgramRoot,$WorkerRoot,$StateRoot,$LegacyStateRoot | Out-Null

$workerSource = Join-Path $PSScriptRoot 'mirror-worker.ps1'
$workerTarget = Join-Path $WorkerRoot 'mirror-worker.ps1'
Copy-Item -LiteralPath $workerSource -Destination $workerTarget -Force

$config = [ordered]@{
  schema_version = 2
  product = 'Research OS'
  root_provider = 'google-drive'
  root_name = 'DRIVE_VIRTUAL_CLOUD'
  root_path = $DriveRoot
  drive_folder_id = $RootId
  local_program_root = $ProgramRoot
  local_state_root = $StateRoot
  worker_mode = 'scheduled-task'
  worker_task = $TaskName
  github_owner = $Owner
  github_mirror = $true
  auto_sync = $true
  restore_enabled = $true
  secrets_policy = 'windows-dpapi-current-user-and-gh-credential-store'
  installed_at = (Get-Date).ToUniversalTime().ToString('o')
}

$configJson = $config | ConvertTo-Json -Depth 6
$configJson | Set-Content -LiteralPath (Join-Path $StateRoot 'bootstrap.json') -Encoding UTF8
# Legacy pointer retained for v0.x migration compatibility.
$configJson | Set-Content -LiteralPath (Join-Path $LegacyStateRoot 'bootstrap.json') -Encoding UTF8
$configJson | Set-Content -LiteralPath (Join-Path $DriveRoot 'runtime\state\bootstrap.active.json') -Encoding UTF8

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$workerTarget`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null
Unregister-ScheduledTask -TaskName $LegacyTaskName -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "Research OS Cloud Root installed: $DriveRoot"
Write-Host "Bootstrap: $StateRoot\bootstrap.json"
Write-Host "Task: $TaskName"
