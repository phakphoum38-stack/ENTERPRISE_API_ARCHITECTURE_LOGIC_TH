[CmdletBinding()]
param(
    [string]$Repository = "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
    [string]$InstallRoot = "D:\ResearchOS-LocalRunner",
    [string]$GitHubAccount = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI is required."
}
if (-not [string]::IsNullOrWhiteSpace($GitHubAccount)) {
    # The Python GUI supplies GH_TOKEN only to this process tree, so account
    # selection does not mutate the user's globally active gh account.
    $authenticatedLogin = [string](gh api user --jq .login)
    if ($LASTEXITCODE -ne 0) { throw "GitHub CLI credential validation failed." }
    if ($authenticatedLogin -ne $GitHubAccount) {
        throw "Selected account mismatch: expected $GitHubAccount but credential belongs to $authenticatedLogin."
    }
} else {
    gh auth status --hostname github.com
    if ($LASTEXITCODE -ne 0) { throw "GitHub CLI authentication failed." }
}
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+

if (Test-Path -LiteralPath $InstallRoot) {
    if (@(Get-ChildItem -LiteralPath $InstallRoot -Force).Count -gt 0) {
        throw "InstallRoot is not empty; refusing to overwrite: $InstallRoot"
    }
} else {
    New-Item -ItemType Directory -Path $InstallRoot | Out-Null
}

$release = Invoke-RestMethod -Uri "https://api.github.com/repos/actions/runner/releases/latest" -Headers @{ "User-Agent" = "ResearchOS-LocalRunner" }
$asset = @($release.assets | Where-Object { $_.name -match '^actions-runner-win-x64-.*\.zip$' } | Select-Object -First 1)
if ($asset.Count -ne 1) { throw "Official Windows x64 runner archive was not found." }
if ([string]$asset[0].digest -notmatch '^sha256:([a-fA-F0-9]{64})$') { throw "Release has no valid SHA-256 digest; refusing unverified download." }
$expectedHash = $Matches[1].ToLowerInvariant()
$zipPath = Join-Path $InstallRoot $asset[0].name
Invoke-WebRequest -Uri $asset[0].browser_download_url -OutFile $zipPath -Headers @{ "User-Agent" = "ResearchOS-LocalRunner" }
$actualHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) { throw "RUNNER_ARCHIVE_SHA256_MISMATCH expected=$expectedHash actual=$actualHash" }
Expand-Archive -LiteralPath $zipPath -DestinationPath $InstallRoot
Remove-Item -LiteralPath $zipPath -Force

$tokenJson = gh api "repos/$Repository/actions/runners/registration-token" --method POST
if ($LASTEXITCODE -ne 0) { throw "Could not obtain runner registration token; repository admin permission may be required." }
$token = [string](($tokenJson | ConvertFrom-Json).token)
if ([string]::IsNullOrWhiteSpace($token)) { throw "GitHub returned an empty registration token." }

$name = "research-os-local-" + [DateTime]::UtcNow.ToString("yyyyMMddHHmmss") + "-" + $PID
Push-Location $InstallRoot
try {
    & .\config.cmd --url "https://github.com/$Repository" --token $token --name $name --labels "research-os-local" --work "_work" --ephemeral --unattended
    if ($LASTEXITCODE -ne 0) { throw "Runner configuration failed: exit $LASTEXITCODE" }
} finally {
    $token = $null
    $tokenJson = $null
    [GC]::Collect()
    Pop-Location
}

$manifest = @(
    "Repository=$Repository"
    "RunnerName=$name"
    "Mode=ephemeral"
    "Label=research-os-local"
    "Release=$($release.tag_name)"
    "Archive=$($asset[0].name)"
    "ArchiveSHA256=$actualHash"
    "ConfiguredUTC=$([DateTime]::UtcNow.ToString('o'))"
)
$manifest | Set-Content -LiteralPath (Join-Path $InstallRoot "research-os-runner-install-manifest.txt") -Encoding utf8

Write-Host "Runner configured. Keep this window open while the single job runs."
Write-Host "Install manifest: $(Join-Path $InstallRoot 'research-os-runner-install-manifest.txt')"
Push-Location $InstallRoot
try {
    & .\run.cmd
    $runnerExit = $LASTEXITCODE
} finally {
    Pop-Location
}
Write-Host "Runner process exit code: $runnerExit"
exit $runnerExit
) { throw "Repository must be owner/name." }

if (Test-Path -LiteralPath $InstallRoot) {
    if (@(Get-ChildItem -LiteralPath $InstallRoot -Force).Count -gt 0) {
        throw "InstallRoot is not empty; refusing to overwrite: $InstallRoot"
    }
} else {
    New-Item -ItemType Directory -Path $InstallRoot | Out-Null
}

$release = Invoke-RestMethod -Uri "https://api.github.com/repos/actions/runner/releases/latest" -Headers @{ "User-Agent" = "ResearchOS-LocalRunner" }
$asset = @($release.assets | Where-Object { $_.name -match '^actions-runner-win-x64-.*\.zip$' } | Select-Object -First 1)
if ($asset.Count -ne 1) { throw "Official Windows x64 runner archive was not found." }
if ([string]$asset[0].digest -notmatch '^sha256:([a-fA-F0-9]{64})$') { throw "Release has no valid SHA-256 digest; refusing unverified download." }
$expectedHash = $Matches[1].ToLowerInvariant()
$zipPath = Join-Path $InstallRoot $asset[0].name
Invoke-WebRequest -Uri $asset[0].browser_download_url -OutFile $zipPath -Headers @{ "User-Agent" = "ResearchOS-LocalRunner" }
$actualHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) { throw "RUNNER_ARCHIVE_SHA256_MISMATCH expected=$expectedHash actual=$actualHash" }
Expand-Archive -LiteralPath $zipPath -DestinationPath $InstallRoot
Remove-Item -LiteralPath $zipPath -Force

$tokenJson = gh api "repos/$Repository/actions/runners/registration-token" --method POST
if ($LASTEXITCODE -ne 0) { throw "Could not obtain runner registration token; repository admin permission may be required." }
$token = [string](($tokenJson | ConvertFrom-Json).token)
if ([string]::IsNullOrWhiteSpace($token)) { throw "GitHub returned an empty registration token." }

$name = "research-os-local-" + [DateTime]::UtcNow.ToString("yyyyMMddHHmmss") + "-" + $PID
Push-Location $InstallRoot
try {
    & .\config.cmd --url "https://github.com/$Repository" --token $token --name $name --labels "research-os-local" --work "_work" --ephemeral --unattended
    if ($LASTEXITCODE -ne 0) { throw "Runner configuration failed: exit $LASTEXITCODE" }
} finally {
    $token = $null
    $tokenJson = $null
    [GC]::Collect()
    Pop-Location
}

$manifest = @(
    "Repository=$Repository"
    "RunnerName=$name"
    "Mode=ephemeral"
    "Label=research-os-local"
    "Release=$($release.tag_name)"
    "Archive=$($asset[0].name)"
    "ArchiveSHA256=$actualHash"
    "ConfiguredUTC=$([DateTime]::UtcNow.ToString('o'))"
)
$manifest | Set-Content -LiteralPath (Join-Path $InstallRoot "research-os-runner-install-manifest.txt") -Encoding utf8

Write-Host "Runner configured. Keep this window open while the single job runs."
Write-Host "Install manifest: $(Join-Path $InstallRoot 'research-os-runner-install-manifest.txt')"
Push-Location $InstallRoot
try {
    & .\run.cmd
    $runnerExit = $LASTEXITCODE
} finally {
    Pop-Location
}
Write-Host "Runner process exit code: $runnerExit"
exit $runnerExit
