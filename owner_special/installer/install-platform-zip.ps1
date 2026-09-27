param(
    [Parameter(Mandatory=$true)][string]$ZipPath,
    [Parameter(Mandatory=$true)][string]$TargetRoot,
    [Parameter(Mandatory=$true)][string]$ExpectedZipSha256,
    [Parameter(Mandatory=$true)][string]$ExpectedSourceSha,
    [string]$DiagnosticLogPath = (Join-Path $env:TEMP 'ResearchOS-Platform-install.log')
)
$ErrorActionPreference = 'Stop'

function Write-Diagnostic([string]$Message) {
    $timestamp = (Get-Date).ToString('o')
    Add-Content -LiteralPath $DiagnosticLogPath -Value ("[$timestamp] " + $Message) -Encoding utf8
}

try { Set-Content -LiteralPath $DiagnosticLogPath -Value '' -Encoding utf8 } catch { }
# Diagnostic preflight is intentionally explicit so installer failures remain observable.
# Phase-E trigger marker: canonical Platform ZIP bootstrap diagnostics.
Write-Diagnostic "START ZipPath=$ZipPath TargetRoot=$TargetRoot ExpectedZipSha256=$ExpectedZipSha256 ExpectedSourceSha=$ExpectedSourceSha"

function Normalize-Hash([string]$Value) { return $Value.Trim().ToLowerInvariant() }

Write-Diagnostic "STEP verify-zip-exists path=$ZipPath"
$zipItem = Get-Item -LiteralPath $ZipPath -ErrorAction SilentlyContinue
if ($null -eq $zipItem) {
    Write-Diagnostic "STEP verify-zip-exists result=MISSING"
    throw "Platform ZIP missing: $ZipPath"
}
Write-Diagnostic "STEP verify-zip-exists result=FOUND length=$($zipItem.Length) full_name=$($zipItem.FullName)"
$actualZipSha = (Get-FileHash -LiteralPath $zipItem.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Diagnostic "STEP verify-zip-sha256 actual=$actualZipSha expected=$(Normalize-Hash $ExpectedZipSha256)"
if ($actualZipSha -ne (Normalize-Hash $ExpectedZipSha256)) {
    throw "Platform ZIP SHA256 mismatch: expected $ExpectedZipSha256 actual $actualZipSha"
}

Write-Diagnostic "STEP validate-zip-entries"
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

Write-Diagnostic "STEP create-staging"
$staging = Join-Path $env:TEMP ("ResearchOS-Platform-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $staging | Out-Null
try {
    Write-Diagnostic "STEP expand-archive staging=$staging"
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $staging -Force

    $manifestPath = Join-Path $staging 'DISTRIBUTION_MANIFEST.json'
    $manifestHashPath = Join-Path $staging 'DISTRIBUTION_MANIFEST.sha256'
    if (-not (Test-Path $manifestPath -PathType Leaf)) { throw 'Platform ZIP is missing DISTRIBUTION_MANIFEST.json' }
    if (-not (Test-Path $manifestHashPath -PathType Leaf)) { throw 'Platform ZIP is missing DISTRIBUTION_MANIFEST.sha256' }

    Write-Diagnostic "STEP validate-manifest"
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    if ([string]$manifest.source_sha -ne $ExpectedSourceSha) {
        throw "Platform source SHA mismatch: expected $ExpectedSourceSha actual $($manifest.source_sha)"
    }
    if ([string]$manifest.product_name -ne 'Research OS') { throw 'Platform product identity mismatch.' }
    if ([string]$manifest.company_name -ne 'Research OS Team') { throw 'Platform company identity mismatch.' }

    Write-Diagnostic "STEP validate-manifest-sha"
    $manifestSha = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $declaredManifestSha = (Get-Content $manifestHashPath -Raw).Trim().Split()[0].ToLowerInvariant()
    if ($manifestSha -ne $declaredManifestSha) {
        throw "Platform manifest SHA mismatch: declared $declaredManifestSha actual $manifestSha"
    }

    Write-Diagnostic "STEP robocopy-to-target"
    New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
    & robocopy.exe $staging $TargetRoot /E /COPY:DAT /J /XJ /R:2 /W:1 /NFL /NDL /NP /TEE /LOG+:"$env:TEMP\\ResearchOS-Platform-robocopy.log" | Out-Host
    $copyCode = $LASTEXITCODE
    Write-Diagnostic "STEP robocopy-result exit_code=$copyCode"
    if ($copyCode -gt 7) { throw "Platform ZIP staged copy failed: robocopy exit code $copyCode" }
    Write-Diagnostic "STEP verify-required-installed-files"
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

    Write-Diagnostic "STEP write-provenance"
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
catch {
    Write-Diagnostic "FAIL message=$($_.Exception.Message)"
    Write-Diagnostic "FAIL category=$($_.CategoryInfo)"
    Write-Diagnostic "FAIL fully_qualified_error_id=$($_.FullyQualifiedErrorId)"
    Write-Diagnostic "FAIL script_stack_trace=$($_.ScriptStackTrace)"
    $robocopyLog = Join-Path $env:TEMP 'ResearchOS-Platform-robocopy.log'
    if (Test-Path $robocopyLog -PathType Leaf) {
        Write-Diagnostic "FAIL robocopy_log=$robocopyLog"
        Get-Content -LiteralPath $robocopyLog -Tail 80 | ForEach-Object { Add-Content -LiteralPath $DiagnosticLogPath -Value ("[ROBOCOPY] " + $_) -Encoding utf8 }
    }
    throw
}
finally {
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue }
}
