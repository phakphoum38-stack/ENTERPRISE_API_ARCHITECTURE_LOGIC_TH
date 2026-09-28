[CmdletBinding()]
param(
  [string]$ServiceName = 'ResearchOSService',
  [int]$ApiPort = 8787,
  [switch]$ConfigureGoogleRedirects
)

$ErrorActionPreference = 'Stop'

function Require-Admin {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($identity)
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Administrator permission is required when -ConfigureGoogleRedirects is used.'
  }
}

$tailscale = Get-Command tailscale.exe -ErrorAction SilentlyContinue
if (-not $tailscale) {
  throw 'tailscale.exe was not found in PATH. Install/sign in to Tailscale first.'
}

try {
  Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$ApiPort/health" -TimeoutSec 5 | Out-Null
}
catch {
  throw "Research OS local API is not healthy at http://127.0.0.1:$ApiPort/health. Start ResearchOSService first."
}

$statusJson = & $tailscale.Source status --json
if ($LASTEXITCODE -ne 0) {
  throw 'Unable to read Tailscale status.'
}

$status = $statusJson | ConvertFrom-Json
$dnsName = [string]$status.Self.DNSName
$dnsName = $dnsName.TrimEnd('.')
if ([string]::IsNullOrWhiteSpace($dnsName)) {
  throw 'Tailscale did not report a MagicDNS hostname for this Windows device.'
}

Write-Host "Research OS local API: http://127.0.0.1:$ApiPort"
Write-Host "Tailscale device DNS : $dnsName"

& $tailscale.Source serve --bg $ApiPort
if ($LASTEXITCODE -ne 0) {
  throw 'Failed to configure Tailscale Serve.'
}

$baseUrl = "https://$dnsName"
$healthUrl = "$baseUrl/health"

Write-Host ''
Write-Host 'Tailscale Serve configured:'
Write-Host "  API base URL : $baseUrl"
Write-Host "  Health URL   : $healthUrl"
Write-Host ''
Write-Host 'iOS IPA build input:'
Write-Host "  RESEARCH_OS_API_BASE_URL=$baseUrl"
Write-Host ''
Write-Host 'Google identity callback:'
Write-Host "  $baseUrl/v1/auth/google/callback"
Write-Host 'Google Workspace callback:'
Write-Host "  $baseUrl/v1/google-workspace/oauth/callback"

if ($ConfigureGoogleRedirects) {
  Require-Admin

  $serviceKey = "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName"
  if (-not (Test-Path $serviceKey)) {
    throw "Windows service registry key was not found: $serviceKey"
  }

  $existing = @(Get-ItemProperty -Path $serviceKey -Name Environment -ErrorAction SilentlyContinue).Environment
  $values = @($existing | Where-Object {
    $_ -notmatch '^RESEARCH_OS_GOOGLE_IDENTITY_REDIRECT_URI=' -and
    $_ -notmatch '^RESEARCH_OS_GOOGLE_REDIRECT_URI='
  })
  $values += "RESEARCH_OS_GOOGLE_IDENTITY_REDIRECT_URI=$baseUrl/v1/auth/google/callback"
  $values += "RESEARCH_OS_GOOGLE_REDIRECT_URI=$baseUrl/v1/google-workspace/oauth/callback"

  New-ItemProperty -Path $serviceKey -Name Environment -PropertyType MultiString -Value $values -Force | Out-Null

  Write-Host ''
  Write-Host 'Service Google redirect URIs updated.'
  Write-Host 'Restarting Research OS Service...'
  Restart-Service -Name $ServiceName -Force
  Start-Sleep -Seconds 2
  Write-Host 'Research OS Service restarted.'
  Write-Host ''
  Write-Host 'IMPORTANT: the same two HTTPS redirect URIs must also be registered in the Google OAuth client configuration.'
}

Write-Host ''
Write-Host 'Verify from the iPhone while Tailscale is connected:'
Write-Host "  $healthUrl"
Write-Host ''
Write-Host 'Keep the Research OS API bound to 127.0.0.1. Tailscale Serve provides the private HTTPS bridge.'
