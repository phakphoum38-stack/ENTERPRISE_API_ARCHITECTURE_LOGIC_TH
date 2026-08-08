[CmdletBinding()]
param(
    [string]$Subject = 'CN=Research OS Development',
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\private\research-os-code-signing.pfx')
)

$ErrorActionPreference = 'Stop'

$outputDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

Write-Host "Creating self-signed code-signing certificate: $Subject"

$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $Subject `
    -CertStoreLocation 'Cert:\CurrentUser\My' `
    -KeyAlgorithm RSA `
    -KeyLength 3072 `
    -HashAlgorithm SHA256

$password = Read-Host 'Enter a strong password for the exported PFX' -AsSecureString

Export-PfxCertificate `
    -Cert $cert `
    -FilePath $OutputPath `
    -Password $password | Out-Null

Write-Host "PFX exported to: $OutputPath"
Write-Host "Certificate thumbprint: $($cert.Thumbprint)"
Write-Host 'Keep the PFX and password outside source control.'
