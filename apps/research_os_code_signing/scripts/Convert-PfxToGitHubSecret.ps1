[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PfxPath
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $PfxPath)) {
    throw "PFX not found: $PfxPath"
}

$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $PfxPath))
$base64 = [Convert]::ToBase64String($bytes)

Write-Host 'Copy the Base64 value below into GitHub Actions secret WINDOWS_SIGNING_CERT_BASE64.'
Write-Host 'Do not commit this value to the repository.'
Write-Output $base64
