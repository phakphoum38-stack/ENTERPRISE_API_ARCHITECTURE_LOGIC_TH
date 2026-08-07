param(
  [ValidateSet('install','uninstall','start','stop','restart','status')]
  [string]$Action = 'status',
  [string]$DataDir = "$env:USERPROFILE\ResearchOSData",
  [string]$ServiceName = 'ResearchOSService'
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Project = Join-Path $RepoRoot 'tools\research_os_service\ResearchOS.ServiceHost.csproj'
$PublishDir = Join-Path $RepoRoot 'tools\research_os_service\publish'
$ServiceExe = Join-Path $PublishDir 'ResearchOS.ServiceHost.exe'

function Test-Admin {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($identity)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Require-Admin {
  if (-not (Test-Admin)) {
    throw 'Administrator permission is required for this Service action.'
  }
}

function Get-ServiceSafe {
  return Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
}

function Wait-ServiceState([string]$Desired, [int]$Seconds = 20) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  do {
    $svc = Get-ServiceSafe
    if ($svc -and $svc.Status.ToString() -eq $Desired) { return $svc }
    Start-Sleep -Milliseconds 350
  } while ((Get-Date) -lt $deadline)
  throw "Service did not reach state $Desired within $Seconds seconds."
}

switch ($Action) {
  'status' {
    $svc = Get-ServiceSafe
    if (-not $svc) {
      Write-Host 'Research OS Service: NOT INSTALLED'
      exit 2
    }
    $startMode = (Get-CimInstance Win32_Service -Filter "Name='$ServiceName'").StartMode
    Write-Host "Research OS Service: $($svc.Status)"
    Write-Host "Service name       : $ServiceName"
    Write-Host "Startup            : $startMode"
    Write-Host "Local API          : http://127.0.0.1:8787"
    exit 0
  }

  'install' {
    Require-Admin

    if (-not (Test-Path $Project)) {
      throw "Service project not found: $Project"
    }

    if (-not (Test-Path $ServiceExe)) {
      $dotnet = Get-Command dotnet.exe -ErrorAction SilentlyContinue
      if (-not $dotnet) {
        throw 'ServiceHost binary is missing and .NET SDK is not installed. Use a packaged Research OS installer or install .NET SDK to build from source.'
      }
      New-Item -ItemType Directory -Force -Path $PublishDir | Out-Null
      & $dotnet.Source publish $Project -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:PublishTrimmed=false -o $PublishDir
      if ($LASTEXITCODE -ne 0 -or -not (Test-Path $ServiceExe)) {
        throw 'Research OS ServiceHost publish failed.'
      }
    }

    $python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if (-not $python) { throw 'python.exe was not found. Install Python or use the packaged runtime.' }

    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'logs') | Out-Null

    [Environment]::SetEnvironmentVariable('RESEARCH_OS_REPO_ROOT', $RepoRoot, 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_DATA_DIR', $DataDir, 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_PYTHON_EXE', $python, 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_API_HOST', '0.0.0.0', 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_API_PORT', '8787', 'Machine')

    $existing = Get-ServiceSafe
    if ($existing) {
      if ($existing.Status -ne 'Stopped') {
        Stop-Service -Name $ServiceName -Force
        Wait-ServiceState 'Stopped' | Out-Null
      }
      sc.exe delete $ServiceName | Out-Null
      Start-Sleep -Seconds 1
    }

    $quotedExe = '"' + $ServiceExe + '"'
    sc.exe create $ServiceName binPath= $quotedExe start= auto DisplayName= 'Research OS API Service' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create Research OS Windows Service.' }

    sc.exe description $ServiceName 'Research OS Local API, Memory, Google Workspace and AI backend service.' | Out-Null
    sc.exe config $ServiceName start= delayed-auto | Out-Null
    sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/10000/restart/30000 | Out-Null
    sc.exe failureflag $ServiceName 1 | Out-Null

    Start-Service -Name $ServiceName
    Wait-ServiceState 'Running' | Out-Null

    Write-Host 'Research OS Service installed and started.'
    Write-Host "Service : $ServiceName"
    Write-Host "API     : http://127.0.0.1:8787"
    Write-Host "Data    : $DataDir"
    Write-Host 'Recovery: restart after 5s, 10s, then 30s'
  }

  'uninstall' {
    Require-Admin
    $svc = Get-ServiceSafe
    if (-not $svc) {
      Write-Host 'Research OS Service is not installed.'
      exit 0
    }
    if ($svc.Status -ne 'Stopped') {
      Stop-Service -Name $ServiceName -Force
      Wait-ServiceState 'Stopped' | Out-Null
    }
    sc.exe delete $ServiceName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Failed to delete Research OS Service.' }
    Write-Host 'Research OS Service uninstalled. Local data was preserved.'
  }

  'start' {
    Require-Admin
    if (-not (Get-ServiceSafe)) { throw 'Research OS Service is not installed.' }
    Start-Service -Name $ServiceName
    Wait-ServiceState 'Running' | Out-Null
    Write-Host 'Research OS Service started.'
  }

  'stop' {
    Require-Admin
    if (-not (Get-ServiceSafe)) { throw 'Research OS Service is not installed.' }
    Stop-Service -Name $ServiceName -Force
    Wait-ServiceState 'Stopped' | Out-Null
    Write-Host 'Research OS Service stopped.'
  }

  'restart' {
    Require-Admin
    if (-not (Get-ServiceSafe)) { throw 'Research OS Service is not installed.' }
    Restart-Service -Name $ServiceName -Force
    Wait-ServiceState 'Running' | Out-Null
    Write-Host 'Research OS Service restarted.'
  }
}
