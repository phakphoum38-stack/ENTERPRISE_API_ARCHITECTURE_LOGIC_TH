[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$ExpectedCommit,
  [string]$AppRoot = (Join-Path $env:ProgramFiles 'Research OS Owner Special')
)

$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
  Write-Error "RELEASE_PROVENANCE_GATE_FAILED: $Message"
  exit 1
}

$ExpectedCommit = $ExpectedCommit.Trim().ToLowerInvariant()
if ([string]::IsNullOrWhiteSpace($ExpectedCommit)) {
  Fail 'Expected commit is empty.'
}

$identityPath = Join-Path $AppRoot 'app\OWNER_BUILD_IDENTITY.json'
$exePath = Join-Path $AppRoot 'app\research_os_owner_special.exe'

if (-not (Test-Path $identityPath -PathType Leaf)) {
  Fail "Installed Owner build identity evidence is missing: $identityPath"
}
if (-not (Test-Path $exePath -PathType Leaf)) {
  Fail "Installed Owner executable is missing: $exePath"
}

try {
  $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
} catch {
  Fail "Installed Owner build identity evidence is invalid JSON: $identityPath"
}

if ($identity.passed -ne $true) {
  Fail 'Installed Owner build identity gate evidence is not passed.'
}
if ([string]$identity.owner_edition -ne 'owner-special') {
  Fail "Installed Owner edition '$($identity.owner_edition)' is not owner-special."
}
if ([string]$identity.file_name -ne 'research_os_owner_special.exe') {
  Fail "Installed Owner identity filename '$($identity.file_name)' is unexpected."
}

$installedCommit = ([string]$identity.commit).Trim().ToLowerInvariant()
if ($installedCommit -ne $ExpectedCommit) {
  Fail "Installed Owner source commit '$installedCommit' != expected release commit '$ExpectedCommit'."
}

$actualSha = (Get-FileHash -LiteralPath $exePath -Algorithm SHA256).Hash.ToLowerInvariant()
$recordedSha = ([string]$identity.sha256).Trim().ToLowerInvariant()
if ([string]::IsNullOrWhiteSpace($recordedSha)) {
  Fail 'Installed Owner identity evidence does not contain an EXE SHA256.'
}
if ($actualSha -ne $recordedSha) {
  Fail "Installed Owner EXE SHA256 '$actualSha' != recorded '$recordedSha'."
}

# A successful PowerShell script invocation does not necessarily reset the caller's
# $LASTEXITCODE. Explicitly clear the global value so workflow steps that inspect it
# do not mistake a previous native command's exit code for this gate's result.
$global:LASTEXITCODE = 0

Write-Host 'RELEASE_PROVENANCE_GATE=PASS'
Write-Host "Expected release commit: $ExpectedCommit"
Write-Host "Installed Owner commit: $installedCommit"
Write-Host "Installed Owner EXE SHA256: $actualSha"
