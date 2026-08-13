$ErrorActionPreference = 'Stop'
$ConfigPath = 'C:\ProgramData\ResearchOS\cloud\bootstrap.json'
$LegacyConfigPath = 'C:\ProgramData\DriveVirtualCloud\bootstrap.json'

if (-not (Test-Path -LiteralPath $ConfigPath)) {
  if (Test-Path -LiteralPath $LegacyConfigPath) { $ConfigPath = $LegacyConfigPath }
  else { throw 'Missing Research OS cloud bootstrap config.' }
}

$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$DriveRoot = [string]$config.root_path
$Owner = [string]$config.github_owner

if (-not (Test-Path -LiteralPath $DriveRoot)) { throw "Drive unavailable: $DriveRoot" }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is not installed or not in PATH' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'gh is not installed or not in PATH' }

& gh auth status *> $null
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI is not authenticated. Run: gh auth login' }

$CacheRoot = Join-Path $env:ProgramData 'ResearchOS\cloud\git-cache'
$BundleRoot = Join-Path $DriveRoot 'github\bundles\full'
$MirrorZipRoot = Join-Path $DriveRoot 'github\mirrors\bare'
$LogRoot = Join-Path $DriveRoot 'logs\github'
New-Item -ItemType Directory -Force -Path $CacheRoot,$BundleRoot,$MirrorZipRoot,$LogRoot | Out-Null

$repos = & gh repo list $Owner --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner'
foreach ($repo in $repos) {
  if ([string]::IsNullOrWhiteSpace($repo)) { continue }
  $name = ($repo -split '/')[-1]
  $mirror = Join-Path $CacheRoot "$name.git"
  $bundle = Join-Path $BundleRoot "$name.bundle"
  $zip = Join-Path $MirrorZipRoot "$name.git.zip"
  try {
    if (Test-Path -LiteralPath $mirror) {
      & git -C $mirror remote update --prune
    } else {
      & git clone --mirror "https://github.com/$repo.git" $mirror
    }
    if ($LASTEXITCODE -ne 0) { throw "git mirror failed ($LASTEXITCODE)" }

    if (Get-Command git-lfs -ErrorAction SilentlyContinue) {
      & git -C $mirror lfs fetch --all 2>$null
    }

    if (Test-Path -LiteralPath $bundle) { Remove-Item -LiteralPath $bundle -Force }
    & git -C $mirror bundle create $bundle --all
    if ($LASTEXITCODE -ne 0) { throw "bundle create failed ($LASTEXITCODE)" }
    & git -C $mirror bundle verify $bundle *> $null
    if ($LASTEXITCODE -ne 0) { throw "bundle verify failed ($LASTEXITCODE)" }

    if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
    Compress-Archive -Path $mirror -DestinationPath $zip -CompressionLevel Optimal

    "$(Get-Date -Format o) OK $repo" | Add-Content -LiteralPath (Join-Path $LogRoot 'mirror-worker.log')
  } catch {
    "$(Get-Date -Format o) FAILED $repo :: $($_.Exception.Message)" | Add-Content -LiteralPath (Join-Path $LogRoot 'mirror-worker.log')
  }
}
