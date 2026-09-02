param(
    [Parameter(Mandatory=$true)][string]$PythonTarget,
    [Parameter(Mandatory=$true)][string]$AppTarget,
    [Parameter(Mandatory=$true)][string]$ServiceHostTarget,
    [int]$Port = 8790,
    [string]$LogPath = (Join-Path $env:TEMP 'ResearchOS-Owner-Quiesce.log')
)

$ErrorActionPreference = 'Stop'

function Write-Diagnostic([string]$Message) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff') $Message"
    try {
        $parent = Split-Path -Parent $LogPath
        if ($parent -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
    }
    catch {
        # Diagnostics must never change the quiesce decision.
    }
    Write-Host $Message
}

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
        Write-Diagnostic "Invalid PID=$ProcessId; refusing to terminate."
        return $false
    }

    $process = Get-CimInstance Win32_Process `
        -Filter "ProcessId = $ProcessId" `
        -ErrorAction SilentlyContinue

    if (-not $process) {
        Write-Diagnostic "PID=$ProcessId is already gone."
        return $true
    }

    if (-not $process.ExecutablePath) {
        Write-Diagnostic "PID=$ProcessId has no executable path; refusing to terminate."
        return $false
    }

    $full = Normalize-Path $process.ExecutablePath

    if (-not $full) {
        Write-Diagnostic "PID=$ProcessId executable path could not be normalized; refusing to terminate."
        return $false
    }

    if (-not ($targets -icontains $full)) {
        Write-Diagnostic "Refusing to terminate foreign process PID=$ProcessId PATH=$full"
        return $false
    }

    Write-Diagnostic "Terminating verified Owner process PID=$ProcessId PATH=$full"

    $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
    $output = & $taskkill /PID $ProcessId /T /F 2>&1
    $taskkillExitCode = $LASTEXITCODE

    if ($output) {
        Write-Diagnostic "taskkill output for PID=$ProcessId: $($output -join [Environment]::NewLine)"
    }

    if ($taskkillExitCode -ne 0) {
        Write-Diagnostic "taskkill failed for verified Owner process PID=$ProcessId EXITCODE=$taskkillExitCode"
        return $false
    }

    Write-Diagnostic "taskkill succeeded for verified Owner process PID=$ProcessId"
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

try {
    Write-Diagnostic '=== OWNER QUIESCE ==='
    Write-Diagnostic "PythonTarget      = $PythonTarget"
    Write-Diagnostic "AppTarget         = $AppTarget"
    Write-Diagnostic "ServiceHostTarget = $ServiceHostTarget"
    Write-Diagnostic "Port              = $Port"
    Write-Diagnostic "LogPath           = $LogPath"
    Write-Diagnostic "Normalized targets = $($targets -join '; ')"

    $success = $true

    Write-Diagnostic 'Checking Owner processes...'
    $running = @(Get-OwnerProcesses)
    Write-Diagnostic "Verified Owner process count = $($running.Count)"

    foreach ($p in $running) {
        if (-not (Stop-OwnerProcess -ProcessId ([int]$p.ProcessId))) {
            $success = $false
        }
    }

    Start-Sleep -Milliseconds 300

    Write-Diagnostic "Checking listeners on port $Port..."
    $listeners = @(Get-OwnerListeners)
    Write-Diagnostic "Listener count on port $Port = $($listeners.Count)"

    foreach ($listener in $listeners) {
        $listenerPid = [int]$listener.OwningProcess
        Write-Diagnostic "Inspecting listener PID=$listenerPid on port $Port"

        $process = Get-CimInstance Win32_Process `
            -Filter "ProcessId = $listenerPid" `
            -ErrorAction SilentlyContinue

        if (-not $process) {
            Write-Diagnostic "Listener PID=$listenerPid disappeared before ownership check."
            continue
        }

        if (-not $process.ExecutablePath) {
            Write-Diagnostic "Port $Port is owned by PID=$listenerPid with no executable path; refusing to terminate."
            $success = $false
            continue
        }

        $full = Normalize-Path $process.ExecutablePath

        if (-not $full -or -not ($targets -icontains $full)) {
            Write-Diagnostic "Port $Port is owned by foreign process PID=$listenerPid PATH=$full"
            Write-Diagnostic 'Refusing to terminate foreign process.'
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

    Write-Diagnostic "Remaining verified Owner processes = $($remainingProcesses.Count)"
    foreach ($p in $remainingProcesses) {
        Write-Diagnostic "Remaining Owner PID=$($p.ProcessId) PATH=$($p.ExecutablePath)"
    }

    Write-Diagnostic "Remaining listeners on port $Port = $($remainingListeners.Count)"
    foreach ($listener in $remainingListeners) {
        Write-Diagnostic "Remaining listener PID=$($listener.OwningProcess)"
    }

    if ($remainingProcesses.Count -gt 0) {
        $success = $false
    }

    if ($remainingListeners.Count -gt 0) {
        $success = $false
    }

    if (-not $success) {
        Write-Diagnostic 'Owner runtime could not be safely quiesced. EXITCODE=5'
        exit 5
    }

    Write-Diagnostic 'Owner runtime quiesced successfully. EXITCODE=0'
    exit 0
}
catch {
    Write-Diagnostic "Unhandled quiesce helper error: $($_.Exception.GetType().FullName): $($_.Exception.Message)"
    Write-Diagnostic 'Owner runtime quiesce helper aborted. EXITCODE=1'
    exit 1
}
