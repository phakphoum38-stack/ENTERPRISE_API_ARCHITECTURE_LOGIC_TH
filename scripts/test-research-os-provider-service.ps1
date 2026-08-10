param(
  [string]$Root = '',
  [string]$BaseUrl = 'http://127.0.0.1:8787'
)

$ErrorActionPreference = 'Stop'

if (-not $Root) {
  $installed = Join-Path $env:ProgramFiles 'Research OS'
  if (Test-Path $installed) {
    $Root = $installed
  }
  else {
    $Root = Split-Path -Parent $PSScriptRoot
  }
}

$Root = [IO.Path]::GetFullPath($Root)
$smoke = Join-Path $Root 'tools\research_os_api\service_provider_smoke.py'
if (-not (Test-Path $smoke)) {
  throw "Research OS service provider smoke script was not found: $smoke"
}

$bundledPython = Join-Path $Root 'runtime\python\python.exe'
if (Test-Path $bundledPython) {
  $python = $bundledPython
}
else {
  $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
  if (-not $pythonCommand) {
    throw 'Python runtime was not found.'
  }
  $python = $pythonCommand.Source
}

$previousBaseUrl = $env:RESEARCH_OS_SMOKE_BASE_URL
try {
  $env:RESEARCH_OS_SMOKE_BASE_URL = $BaseUrl
  & $python $smoke
  $code = $LASTEXITCODE
}
finally {
  $env:RESEARCH_OS_SMOKE_BASE_URL = $previousBaseUrl
}

if ($code -ne 0) {
  if ($code -eq 2) {
    throw 'No real provider credential is configured inside the running Research OS Service.'
  }
  if ($code -eq 3) {
    throw 'Research OS Service is unavailable or its credential-status endpoint could not be verified.'
  }
  throw "Research OS live provider smoke failed with exit code $code."
}

Write-Host 'Research OS live provider smoke: PASS'
