param(
  [Parameter(Mandatory=$true)][ValidateSet('set','get','delete','exists')][string]$Action,
  [Parameter(Mandatory=$true)][string]$Id,
  [string]$SecretBase64 = ''
)

$ErrorActionPreference = 'Stop'
$base = Join-Path $env:LOCALAPPDATA 'ResearchOS\secrets'
New-Item -ItemType Directory -Force -Path $base | Out-Null
$safeId = ($Id -replace '[^a-zA-Z0-9_.-]', '_')
$path = Join-Path $base "$safeId.dpapi"

switch ($Action) {
  'set' {
    if ([string]::IsNullOrWhiteSpace($SecretBase64)) { throw 'SecretBase64 is required for set.' }
    $plain = [Convert]::FromBase64String($SecretBase64)
    try {
      $encrypted = [Security.Cryptography.ProtectedData]::Protect(
        $plain,
        $null,
        [Security.Cryptography.DataProtectionScope]::CurrentUser
      )
      [IO.File]::WriteAllBytes($path, $encrypted)
      Write-Output 'ok'
    } finally {
      [Array]::Clear($plain, 0, $plain.Length)
    }
  }
  'get' {
    if (-not (Test-Path $path)) { exit 3 }
    $encrypted = [IO.File]::ReadAllBytes($path)
    $plain = [Security.Cryptography.ProtectedData]::Unprotect(
      $encrypted,
      $null,
      [Security.Cryptography.DataProtectionScope]::CurrentUser
    )
    try {
      Write-Output ([Convert]::ToBase64String($plain))
    } finally {
      [Array]::Clear($plain, 0, $plain.Length)
    }
  }
  'delete' {
    Remove-Item $path -Force -ErrorAction SilentlyContinue
    Write-Output 'ok'
  }
  'exists' {
    if (Test-Path $path) { Write-Output 'true' } else { Write-Output 'false' }
  }
}
