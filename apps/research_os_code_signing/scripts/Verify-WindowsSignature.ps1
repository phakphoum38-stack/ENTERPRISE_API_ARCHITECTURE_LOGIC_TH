[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ArtifactPath
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ArtifactPath)) {
    throw "Artifact not found: $ArtifactPath"
}

$signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if ($signtool) {
    & $signtool.Source verify /pa /v $ArtifactPath
    if ($LASTEXITCODE -ne 0) {
        throw "signtool verify failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Warning 'signtool.exe not found; using Get-AuthenticodeSignature as a fallback.'
    $signature = Get-AuthenticodeSignature -FilePath $ArtifactPath
    $signature | Format-List Status, StatusMessage, SignerCertificate, TimeStamperCertificate

    if ($signature.Status -ne 'Valid') {
        throw "Authenticode signature status is $($signature.Status)"
    }
}

Write-Host "Signature verified: $ArtifactPath"
