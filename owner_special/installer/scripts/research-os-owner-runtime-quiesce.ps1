param(
    [Parameter(Mandatory=$true)][string]$PythonTarget,
    [Parameter(Mandatory=$true)][string]$AppTarget,
    [Parameter(Mandatory=$true)][string]$ServiceHostTarget,
    [int]$Port = 8790
)

$ErrorActionPreference = 'Stop'

function Normalize-Path([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    try {
        return [IO.Path]::GetFullPath($Path)
    }
    catch {
        return $null
    }
}

$targets = @(
    $PythonTarget,
    $AppTarget,
    $ServiceHostTarget
) |
ForEach-Object {
    Normalize-Path $_
} |
Where-Object {
    $_
}

function Stop-OwnerProcess {
    param(
        [Parameter(Mandatory=$true)][int]$ProcessId
    )

    if ($ProcessId -le 0) {
        return $false
    }

    $process = Get-CimInstance Win32_Process `
        -Filter "ProcessId = $ProcessId" `
        -ErrorAction SilentlyContinue

    if (-not $process) {
        Write-Host "PID=$ProcessId is already gone."
        return $true
    }

    if (-not $process.ExecutablePath) {
        Write-Host "PID=$ProcessId has no executable path; refusing to terminate."
        return $false
    }

    $full = Normalize-Path $process.ExecutablePath

    if (-not $full) {
        Write-Host "PID=$ProcessId executable path could not be normalized; refusing to terminate."
        return $false
    }

    if (-not ($targets -icontains $full)) {
        Write-Host "Refusing to terminate foreign process PID=$ProcessId PATH=$full"
        return $false
    }

    Write-Host "Terminating verified Owner process PID=$ProcessId PATH=$full"

    $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
    $output = & $taskkill /PID $ProcessId /T /F 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "taskkill failed for verified Owner process PID=$ProcessId"
        if ($output) {
            Write-Host ($output -join [Environment]::NewLine)
        }
        return $false
    }

    return $true
}

function Get-OwnerProcesses {
    return @(
        Get-CimInstance Win32_Process -ErrorAction Stop |
        Where-Object {
            if (-not $_.ExecutablePath) {
                return $false
            }

            $full = Normalize-Path $_.ExecutablePath

            return $full -and ($targets -icontains $full)
        }
    )
}

function Get-OwnerListeners {
    return @(
        Get-NetTCPConnection -ErrorAction Stop |
        Where-Object {
            $_.LocalPort -eq $Port -and
            $_.State -eq 'Listen'
        }
    )
}

Write-Host "=== OWNER QUIESCE ==="
Write-Host "PythonTarget      = $PythonTarget"
Write-Host "AppTarget         = $AppTarget"
Write-Host "ServiceHostTarget = $ServiceHostTarget"
Write-Host "Port              = $Port"
Write-Host ""

$success = $true

Write-Host "Checking Owner processes..."
$running = @(Get-OwnerProcesses)

foreach ($p in $running) {
    if (-not (Stop-OwnerProcess -ProcessId ([int]$p.ProcessId))) {
        $success = $false
    }
}

Start-Sleep -Milliseconds 300

Write-Host ""
Write-Host "Checking listeners on port $Port..."

$listeners = @(Get-OwnerListeners)

foreach ($listener in $listeners) {
    $listenerPid = [int]$listener.OwningProcess

    $process = Get-CimInstance Win32_Process `
        -Filter "ProcessId = $listenerPid" `
        -ErrorAction SilentlyContinue

    if (-not $process) {
        continue
    }

    if (-not $process.ExecutablePath) {
        Write-Host "Port $Port is owned by PID=$listenerPid with no executable path; refusing to terminate."
        $success = $false
        continue
    }

    $full = Normalize-Path $process.ExecutablePath

    if (-not $full -or -not ($targets -icontains $full)) {
        Write-Host "Port $Port is owned by foreign process PID=$listenerPid PATH=$full"
        Write-Host "Refusing to terminate foreign process."
        $success = $false
        continue
    }

    if (-not (Stop-OwnerProcess -ProcessId $listenerPid)) {
        $success = $false
    }
}

Start-Sleep -Milliseconds 500

$remainingProcesses = @(Get-OwnerProcesses)
$remainingListeners = @(Get-OwnerListeners)

if ($remainingProcesses.Count -gt 0) {
    Write-Host "Owner processes still running: $($remainingProcesses.Count)"
    $success = $false
}

if ($remainingListeners.Count -gt 0) {
    Write-Host "Port $Port still has listener(s): $($remainingListeners.Count)"
    foreach ($listener in $remainingListeners) {
        Write-Host "Remaining listener PID=$($listener.OwningProcess)"
    }
    $success = $false
}

if (-not $success) {
    Write-Host "Owner runtime could not be safely quiesced."
    exit 5
}

Write-Host "Owner runtime quiesced successfully."
exit 0
