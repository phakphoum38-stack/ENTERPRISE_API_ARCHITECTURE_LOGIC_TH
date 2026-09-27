param(
    [Parameter(Mandatory=$true)][string]$ZipPath,
    [Parameter(Mandatory=$true)][string]$TargetRoot,
    [Parameter(Mandatory=$true)][string]$ExpectedZipSha256,
    [Parameter(Mandatory=$true)][string]$ExpectedSourceSha
)
$ErrorActionPreference = 'Stop'

function Normalize-Hash([string]$Value) { return $Value.Trim().ToLowerInvariant() }

if (-not (Test-Path $ZipPath -PathType Leaf)) { throw "Platform ZIP missing: $ZipPath" }
$actualZipSha = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualZipSha -ne (Normalize-Hash $ExpectedZipSha256)) {
    throw "Platform ZIP SHA256 mismatch: expected $ExpectedZipSha256 actual $actualZipSha"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    foreach ($entry in $archive.Entries) {
        $name = $entry.FullName.Replace('\','/')
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        if ($name.StartsWith('/') -or $name -match '^[A-Za-z]:') { throw "Unsafe absolute ZIP entry: $name" }
        $segments = $name.Split('/')
        if ($segments -contains '..') { throw "Unsafe parent ZIP entry: $name" }
    }
} finally {
    $archive.Dispose()
}

$staging = Join-Path $env:TEMP ("ResearchOS-Platform-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $staging | Out-Null
try {
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $staging -Force

    $manifestPath = Join-Path $staging 'DISTRIBUTION_MANIFEST.json'
    $manifestHashPath = Join-Path $staging 'DISTRIBUTION_MANIFEST.sha256'
    if (-not (Test-Path $manifestPath -PathType Leaf)) { throw 'Platform ZIP is missing DISTRIBUTION_MANIFEST.json' }
    if (-not (Test-Path $manifestHashPath -PathType Leaf)) { throw 'Platform ZIP is missing DISTRIBUTION_MANIFEST.sha256' }

    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    if ([string]$manifest.source_sha -ne $ExpectedSourceSha) {
        throw "Platform source SHA mismatch: expected $ExpectedSourceSha actual $($manifest.source_sha)"
    }
    if ([string]$manifest.product_name -ne 'Research OS') { throw 'Platform product identity mismatch.' }
    if ([string]$manifest.company_name -ne 'Research OS Team') { throw 'Platform company identity mismatch.' }

    $manifestSha = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $declaredManifestSha = (Get-Content $manifestHashPath -Raw).Trim().Split()[0].ToLowerInvariant()
    if ($manifestSha -ne $declaredManifestSha) {
        throw "Platform manifest SHA mismatch: declared $declaredManifestSha actual $manifestSha"
    }

    New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
    & robocopy.exe $staging $TargetRoot /E /COPY:DAT /J /XJ /R:2 /W:1 /NFL /NDL /NP /TEE /LOG+:"$env:TEMP\\ResearchOS-Platform-robocopy.log" | Out-Host
    $copyCode = $LASTEXITCODE
    if ($copyCode -gt 7) { throw "Platform ZIP staged copy failed: robocopy exit code $copyCode" }
    foreach ($required in @(
        'app\\research_os_flutter.exe',
        'owner_special\\app\\research_os_owner_special.exe',
        'owner_special\\scripts\\install-owner-service.ps1',
        'scripts\\research-os-service.ps1',
        'service_host\\ResearchOS.ServiceHost.exe',
        'service_host\\ResearchOS.Owner.ServiceHost.exe'
    )) {
        if (-not (Test-Path (Join-Path $TargetRoot $required) -PathType Leaf)) { throw "Platform ZIP installation is incomplete; missing $required" }
    }

    $provenance = [ordered]@{
        schema = 'research-os.owner-special-platform-install.v1'
        source_sha = [string]$manifest.source_sha
        platform_zip_sha256 = $actualZipSha
        distribution_manifest_sha256 = $manifestSha
        release_authority = 'FINAL_GATE'
        installer_role = 'OWNER_SPECIAL'
    }
    $provenance | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $TargetRoot 'OWNER_SPECIAL_PLATFORM_INSTALL_PROVENANCE.json') -Encoding utf8
    Write-Host "OWNER_SPECIAL_PLATFORM_INSTALL=PASS source_sha=$ExpectedSourceSha zip_sha256=$actualZipSha"
}
finally {
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue }
}
