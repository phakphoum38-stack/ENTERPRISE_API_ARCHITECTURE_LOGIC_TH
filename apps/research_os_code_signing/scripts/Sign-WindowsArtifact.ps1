[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PfxPath,

    [Parameter(Mandatory = $true)]
    [string]$ArtifactPath,

    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $PfxPath)) {
    throw "PFX not found: $PfxPath"
}

if (-not (Test-Path $ArtifactPath)) {
    throw "Artifact not found: $ArtifactPath"
}

$signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if (-not $signtool) {
    throw 'signtool.exe was not found. Install the Windows SDK and ensure signtool.exe is on PATH.'
}

$password = Read-Host 'Enter the PFX password' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
try {
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)

    & $signtool.Source sign `
        /f $PfxPath `
        /p $plainPassword `
        /fd SHA256 `
        /tr $TimestampUrl `
        /td SHA256 `
        $ArtifactPath

    if ($LASTEXITCODE -ne 0) {
        throw "signtool sign failed with exit code $LASTEXITCODE"
    }
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    $plainPassword = $null
}

Write-Host "Signed successfully: $ArtifactPath"
