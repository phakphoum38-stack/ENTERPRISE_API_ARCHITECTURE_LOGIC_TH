[CmdletBinding()]
param(
    [string]$Repository = "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
    [string]$InstallRoot = "D:\ResearchOS-LocalRunner"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if (-not (Get-Command "gh" -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required. Install it and sign in before running this script."
}
gh auth status --hostname github.com
if ($LASTEXITCODE -ne 0) { throw "GitHub CLI authentication is not ready." }
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') { throw "Repository must be owner/name." }

if (Test-Path -LiteralPath $InstallRoot) {
    $existing = @(Get-ChildItem -LiteralPath $InstallRoot -Force -ErrorAction Stop)
    if ($existing.Count -gt 0) {
        throw "InstallRoot is not empty; refusing to overwrite or delete existing files: $InstallRoot"
    }
} else {
    New-Item -ItemType Directory -Path $InstallRoot | Out-Null
}

# Download the official GitHub Actions runner release for Windows x64.
$headers = @{ "User-Agent" = "ResearchOS-LocalRunner-Bootstrap"; "Accept" = "application/vnd.github+json" }
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/actions/runner/releases/latest" -Headers $headers
$asset = @($release.assets | Where-Object { $_.name -match '^actions-runner-win-x64-.*\.zip$' } | Select-Object -First 1)
if ($asset.Count -ne 1) { throw "Could not identify the official Windows x64 runner asset in the latest release." }

$zipPath = Join-Path $InstallRoot $asset[0].name
Invoke-WebRequest -Uri $asset[0].browser_download_url -OutFile $zipPath -Headers @{ "User-Agent" = "ResearchOS-LocalRunner-Bootstrap" }
$zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
Expand-Archive -LiteralPath $zipPath -DestinationPath $InstallRoot
Remove-Item -LiteralPath $zipPath -Force

# Registration tokens are short-lived. Never write the token to disk or print it.
$tokenResponse = gh api "repos/$Repository/actions/runners/registration-token" --method POST
if ($LASTEXITCODE -ne 0) { throw "Could not obtain a runner registration token. Repository admin permission may be required." }
$tokenObject = $tokenResponse | ConvertFrom-Json
$registrationToken = [string]$tokenObject.token
if ([string]::IsNullOrWhiteSpace($registrationToken)) { throw "GitHub returned an empty registration token." }

$runnerName = "research-os-local-$([DateTime]::UtcNow.ToString('yyyyMMddHHmmss'))-$PID"
Push-Location $InstallRoot
try {
    $configArgs = @(
        "--url", "https://github.com/$Repository",
        "--token", $registrationToken,
        "--name", $runnerName,
        "--labels", "research-os-local",
        "--work", "_work",
        "--ephemeral",
        "--unattended"
    )
    & .\config.cmd @configArgs
    if ($LASTEXITCODE -ne 0) { throw "Runner configuration failed with exit code $LASTEXITCODE." }
} finally {
    $registrationToken = $null
    $tokenObject = $null
    [GC]::Collect()
    Pop-Location
}

@"
Repository: $Repository
Runner name: $runnerName
Runner mode: ephemeral
Custom label: research-os-local
Runner release: $($release.tag_name)
Downloaded asset: $($asset[0].name)
Downloaded asset SHA-256: $zipHash
Configured UTC: $([DateTime]::UtcNow.ToString('o'))
"@ | Set-Content -LiteralPath (Join-Path $InstallRoot "research-os-runner-install-manifest.txt") -Encoding utf8

Write-Host ""
Write-Host "Runner configured. Starting it in the foreground; keep this window open."
Write-Host "Dispatch .github/workflows/local-runner-evidence.yml from GitHub and select the target branch/SHA."
Write-Host "The runner is ephemeral and will accept one job. Logs and install manifest remain at: $InstallRoot"
Push-Location $InstallRoot
try {
    & .\run.cmd
    $runnerExit = $LASTEXITCODE
} finally {
    Pop-Location
}
Write-Host "Runner process exit code: $runnerExit"
exit $runnerExit
