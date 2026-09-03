[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$ExePath,
  [string]$ExpectedFileName = 'Research OS Friend.exe',
  [string]$ExpectedProductName = 'Research OS Friend',
  [string]$ExpectedInternalName = 'ResearchOSFriend',
  [string]$ExpectedCompanyName = 'Research OS Team',
  [string]$ExpectedOwnerEdition = 'owner-special',
  [string]$ExpectedManifestPath = (Join-Path $PSScriptRoot '..\OWNER_MANIFEST.json')
)

$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
  Write-Error "BUILD_IDENTITY_GATE_FAILED: $Message"
  exit 1
}

if (-not (Test-Path $ExePath -PathType Leaf)) {
  Fail "EXE does not exist: $ExePath"
}

$file = Get-Item -LiteralPath $ExePath
if ($file.Name -ne $ExpectedFileName) {
  Fail "Unexpected executable filename '$($file.Name)'; expected '$ExpectedFileName'."
}

$vi = $file.VersionInfo
$checks = @{
  ProductName = $vi.ProductName
  InternalName = $vi.InternalName
  CompanyName = $vi.CompanyName
  OriginalFilename = $vi.OriginalFilename
  FileDescription = $vi.FileDescription
}

if ($vi.ProductName -ne $ExpectedProductName) { Fail "ProductName '$($vi.ProductName)' != '$ExpectedProductName'." }
if ($vi.InternalName -ne $ExpectedInternalName) { Fail "InternalName '$($vi.InternalName)' != '$ExpectedInternalName'." }
if ($vi.CompanyName -ne $ExpectedCompanyName) { Fail "CompanyName '$($vi.CompanyName)' != '$ExpectedCompanyName'." }
if ($vi.OriginalFilename -ne $ExpectedFileName) { Fail "OriginalFilename '$($vi.OriginalFilename)' != '$ExpectedFileName'." }
if ($vi.FileDescription -ne $ExpectedProductName) { Fail "FileDescription '$($vi.FileDescription)' != '$ExpectedProductName'." }

if (-not (Test-Path $ExpectedManifestPath -PathType Leaf)) {
  Fail "Owner manifest missing: $ExpectedManifestPath"
}

$manifest = Get-Content -LiteralPath $ExpectedManifestPath -Raw | ConvertFrom-Json
if ($manifest.edition -ne $ExpectedOwnerEdition) {
  Fail "Manifest edition '$($manifest.edition)' != '$ExpectedOwnerEdition'."
}
if ($manifest.owner_only -ne $true) {
  Fail 'Owner manifest is not owner_only=true.'
}

$sha = (Get-FileHash -LiteralPath $ExePath -Algorithm SHA256).Hash
$result = [ordered]@{
  gate = 'owner-special-build-identity'
  passed = $true
  executable = $file.FullName
  file_name = $file.Name
  sha256 = $sha
  product_name = $vi.ProductName
  internal_name = $vi.InternalName
  original_filename = $vi.OriginalFilename
  file_description = $vi.FileDescription
  company_name = $vi.CompanyName
  owner_edition = $manifest.edition
  owner_only = [bool]$manifest.owner_only
  manifest_version = $manifest.version
  commit = $env:GITHUB_SHA
}

$resultPath = Join-Path $file.DirectoryName 'OWNER_BUILD_IDENTITY.json'
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding utf8
Write-Host 'BUILD_IDENTITY_GATE=PASS'
$result | ConvertTo-Json -Depth 5
