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
$BundledPython = Join-Path $RepoRoot 'runtime\python\python.exe'
$ApiPort = 8787
$ProviderEnvironmentNames = @(
  'RESEARCH_OS_PROVIDER',
  'RESEARCH_OS_SEARCH_PROVIDER',
  'RESEARCH_OS_OPENAI_API_KEY',
  'OPENAI_API_KEY',
  'RESEARCH_OS_OPENAI_RESPONSES_ENDPOINT',
  'RESEARCH_OS_OPENAI_RESPONSES_MODEL'
)

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

function Get-PortListeners([int]$Port = $ApiPort) {
  return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Test-ResearchOsApiProcess([int]$ProcessId) {
  $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
  if (-not $process) { return $false }

  $commandLine = [string]$process.CommandLine
  $executablePath = [string]$process.ExecutablePath
  $normalizedRoot = [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
  $normalizedBundledRoot = [IO.Path]::GetFullPath((Join-Path $RepoRoot 'runtime\python')).TrimEnd('\')

  $isBundledPython = $false
  if ($executablePath) {
    try {
      $normalizedExe = [IO.Path]::GetFullPath($executablePath)
      $isBundledPython = $normalizedExe.StartsWith(
        $normalizedBundledRoot + '\',
        [StringComparison]::OrdinalIgnoreCase
      )
    }
    catch {
      $isBundledPython = $false
    }
  }

  $isRepoRenderServer = $false
  if ($commandLine -and $commandLine -match '(?i)render_server\.py') {
    $isRepoRenderServer = $commandLine.IndexOf(
      $normalizedRoot,
      [StringComparison]::OrdinalIgnoreCase
    ) -ge 0
  }

  if ($isBundledPython -or $isRepoRenderServer) {
    Write-Host "Research OS API listener PID $ProcessId identified."
    Write-Host "Executable : $executablePath"
    Write-Host "CommandLine: $commandLine"
    return $true
  }

  Write-Warning "PID $ProcessId is listening on port $ApiPort but does not look like a Research OS API process. It will not be terminated."
  Write-Warning "Executable : $executablePath"
  Write-Warning "CommandLine: $commandLine"
  return $false
}

function Stop-ResearchOsApiListener([int]$Seconds = 15) {
  $listeners = Get-PortListeners
  if (-not $listeners) { return }

  foreach ($listener in $listeners) {
    $pidToStop = [int]$listener.OwningProcess
    if ($pidToStop -le 0) { continue }

    if (Test-ResearchOsApiProcess -ProcessId $pidToStop) {
      Write-Host "Stopping orphan Research OS API process tree PID $pidToStop..."
      & taskkill.exe /PID $pidToStop /T /F | Out-Host
      if ($LASTEXITCODE -ne 0) {
        Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue
      }
    }
  }

  $deadline = (Get-Date).AddSeconds($Seconds)
  do {
    $remaining = Get-PortListeners
    if (-not $remaining) {
      Write-Host "Research OS API port $ApiPort is free."
      return
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $deadline)

  $remaining = Get-PortListeners
  foreach ($listener in $remaining) {
    $pidRemaining = [int]$listener.OwningProcess
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$pidRemaining" -ErrorAction SilentlyContinue
    Write-Warning "Port $ApiPort listener remains: PID=$pidRemaining Executable=$($process.ExecutablePath) CommandLine=$($process.CommandLine)"
  }
  throw "Port $ApiPort still has a listener after Research OS service shutdown."
}

function Stop-ResearchOsServiceAndApi {
  $svc = Get-ServiceSafe
  if ($svc -and $svc.Status -ne 'Stopped') {
    Stop-Service -Name $ServiceName -Force
    Wait-ServiceState 'Stopped' | Out-Null
  }

  # A service can report Stopped before a spawned Python process has fully exited.
  # Only terminate listeners that can be positively identified as Research OS.
  Stop-ResearchOsApiListener
}

function Get-PreservedProviderEnvironment {
  $serviceKey = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\$ServiceName"
  if (-not (Test-Path $serviceKey)) { return @() }

  try {
    $entries = @((Get-ItemProperty -Path $serviceKey -Name Environment -ErrorAction Stop).Environment)
  }
  catch {
    return @()
  }

  return @(
    $entries | Where-Object {
      if (-not $_) { return $false }
      $separator = $_.IndexOf('=')
      if ($separator -le 0) { return $false }
      $name = $_.Substring(0, $separator)
      return $ProviderEnvironmentNames -contains $name
    }
  )
}

function Set-ServiceEnvironment(
  [string]$PythonPath,
  [string[]]$PreservedProviderEnvironment = @()
) {
  $serviceKey = "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName"
  if (-not (Test-Path $serviceKey)) {
    throw "Windows Service registry key was not created: $serviceKey"
  }

  $values = @(
    "RESEARCH_OS_REPO_ROOT=$RepoRoot",
    "RESEARCH_OS_DATA_DIR=$DataDir",
    "RESEARCH_OS_PYTHON_EXE=$PythonPath",
    'RESEARCH_OS_API_HOST=127.0.0.1',
    "RESEARCH_OS_API_PORT=$ApiPort"
  )
  $values += @($PreservedProviderEnvironment)

  New-ItemProperty -Path $serviceKey -Name Environment -PropertyType MultiString -Value $values -Force | Out-Null
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
    Write-Host "Local API          : http://127.0.0.1:$ApiPort"
    exit 0
  }

  'install' {
    Require-Admin

    if (-not (Test-Path $ServiceExe)) {
      if (-not (Test-Path $Project)) {
        throw "ServiceHost binary/project not found under: $RepoRoot"
      }
      $dotnet = Get-Command dotnet.exe -ErrorAction SilentlyContinue
      if (-not $dotnet) {
        throw 'ServiceHost binary is missing and .NET SDK is not installed. Use the packaged Research OS installer.'
      }
      New-Item -ItemType Directory -Force -Path $PublishDir | Out-Null
      & $dotnet.Source publish $Project -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:PublishTrimmed=false -o $PublishDir
      if ($LASTEXITCODE -ne 0 -or -not (Test-Path $ServiceExe)) {
        throw 'Research OS ServiceHost publish failed.'
      }
    }

    if (Test-Path $BundledPython) {
      $python = $BundledPython
      Write-Host "Using bundled Python runtime: $python"
    }
    else {
      $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
      if (-not $pythonCommand) {
        throw 'Python runtime was not found. Install using the packaged Research OS installer or install Python for development mode.'
      }
      $python = $pythonCommand.Source
      Write-Host "Using system Python runtime: $python"
    }

    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'logs') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'sessions') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'database') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'artifacts') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'backups') | Out-Null

    [Environment]::SetEnvironmentVariable('RESEARCH_OS_REPO_ROOT', $RepoRoot, 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_DATA_DIR', $DataDir, 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_PYTHON_EXE', $python, 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_API_HOST', '127.0.0.1', 'Machine')
    [Environment]::SetEnvironmentVariable('RESEARCH_OS_API_PORT', "$ApiPort", 'Machine')

    $preservedProviderEnvironment = Get-PreservedProviderEnvironment
    $existing = Get-ServiceSafe
    if ($existing) {
      Stop-ResearchOsServiceAndApi
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
    Set-ServiceEnvironment -PythonPath $python -PreservedProviderEnvironment $preservedProviderEnvironment

    Start-Service -Name $ServiceName
    Wait-ServiceState 'Running' | Out-Null

    Write-Host 'Research OS Service installed and started.'
    Write-Host "Service : $ServiceName"
    Write-Host "API     : http://127.0.0.1:$ApiPort"
    Write-Host "Data    : $DataDir"
    Write-Host "Runtime : $python"
    Write-Host 'Recovery: restart after 5s, 10s, then 30s'
  }

  'uninstall' {
    Require-Admin
    $svc = Get-ServiceSafe
    if (-not $svc) {
      # The service may already be gone while a child process from a previous
      # shutdown is still alive. Clean only positively identified Research OS listeners.
      Stop-ResearchOsApiListener
      Write-Host 'Research OS Service is not installed.'
      exit 0
    }

    Stop-ResearchOsServiceAndApi
    sc.exe delete $ServiceName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Failed to delete Research OS Service.' }

    $deadline = (Get-Date).AddSeconds(15)
    do {
      if (-not (Get-ServiceSafe)) { break }
      Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    if (Get-ServiceSafe) {
      throw 'Research OS Service is still registered after delete.'
    }

    Stop-ResearchOsApiListener
    foreach ($name in @(
      'RESEARCH_OS_REPO_ROOT',
      'RESEARCH_OS_DATA_DIR',
      'RESEARCH_OS_PYTHON_EXE',
      'RESEARCH_OS_API_HOST',
      'RESEARCH_OS_API_PORT'
    )) {
      [Environment]::SetEnvironmentVariable($name, $null, 'Machine')
    }
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
    Stop-ResearchOsServiceAndApi
    Write-Host 'Research OS Service stopped and API listener released.'
  }

  'restart' {
    Require-Admin
    if (-not (Get-ServiceSafe)) { throw 'Research OS Service is not installed.' }
    Stop-ResearchOsServiceAndApi
    Start-Service -Name $ServiceName
    Wait-ServiceState 'Running' | Out-Null
    Write-Host 'Research OS Service restarted.'
  }
}
