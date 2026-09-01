#define MyAppName "Research OS Owner Special"
#define MyAppVersion "1.3.1-owner"
#define MyAppPublisher "Research OS Owner"
#define MyAppExeName "research_os_owner_special.exe"

[Setup]
AppId={{5C14D248-10A2-4F7B-A9A8-3AC5B0FCB217}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Research OS Owner Special
DefaultGroupName=Research OS Owner Special
UsePreviousAppDir=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir=output
OutputBaseFilename=Research-OS-Owner-Special-Setup-1.3.1-x64
UninstallDisplayName=Research OS Owner Special
UninstallDisplayIcon={app}\app\{#MyAppExeName}
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{commonappdata}\ResearchOSOwnerSpecial"
Name: "{commonappdata}\ResearchOSOwnerSpecial\owners"
Name: "{commonappdata}\ResearchOSOwnerSpecial\service"

[Icons]
Name: "{group}\Research OS Owner Special"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"
Name: "{autodesktop}\Research OS Owner Special"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "startapp"; Description: "Launch Owner Special after installation"; GroupDescription: "After setup:"; Flags: checkedonce

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action install -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"""; StatusMsg: "Installing Owner Friend Windows Service..."; Flags: runhidden waituntilterminated
Filename: "{app}\app\{#MyAppExeName}"; Description: "Launch Research OS Owner Special"; WorkingDir: "{app}\app"; Flags: nowait postinstall skipifsilent; Tasks: startapp

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action uninstall -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"""; Flags: runhidden waituntilterminated; RunOnceId: "ResearchOSOwnerFriendServiceUninstall"

[Code]
function OwnerFriendServiceIsStopped(): Boolean;
var
  ResultCode: Integer;
  CmdExe: String;
begin
  CmdExe := ExpandConstant('{cmd}');
  Result := Exec(CmdExe, '/C sc.exe query ResearchOSOwnerFriendService | findstr /C:"STOPPED" >nul', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function QuiesceOwnerRuntime(): Boolean;
var
  ResultCode: Integer;
  PowerShellExe: String;
  PythonPath: String;
  AppPath: String;
  ServiceHostPath: String;
  GuardPath: String;
  GuardScript: String;
  Parameters: String;
begin
  PythonPath := ExpandConstant('{app}\runtime\python\python.exe');
  AppPath := ExpandConstant('{app}\app\{#MyAppExeName}');
  ServiceHostPath := ExpandConstant('{app}\service_host\ResearchOS.Owner.ServiceHost.exe');
  GuardPath := ExpandConstant('{tmp}\research-os-owner-runtime-quiesce.ps1');
  GuardScript :=
    'param([Parameter(Mandatory=$true)][string]$PythonTarget,[Parameter(Mandatory=$true)][string]$AppTarget,[Parameter(Mandatory=$true)][string]$ServiceHostTarget,[int]$Port=8790)' + #13#10 +
    '$ErrorActionPreference = ''Stop''' + #13#10 +
    'function Normalize-Path([string]$Path) {' + #13#10 +
    '  if ([string]::IsNullOrWhiteSpace($Path)) { return $null }' + #13#10 +
    '  try { return [IO.Path]::GetFullPath($Path) } catch { return $null }' + #13#10 +
    '}' + #13#10 +
    '$targets = @($PythonTarget,$AppTarget,$ServiceHostTarget) | ForEach-Object { Normalize-Path $_ } | Where-Object { $_ }' + #13#10 +
    'function Get-OwnerProcesses {' + #13#10 +
    '  return @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {' + #13#10 +
    '    if (-not $_.ExecutablePath) { return $false }' + #13#10 +
    '    $full = Normalize-Path $_.ExecutablePath' + #13#10 +
    '    return $full -and ($targets -icontains $full)' + #13#10 +
    '  })' + #13#10 +
    '}' + #13#10 +
    'function Get-OwnerListeners {' + #13#10 +
    '  return @(Get-NetTCPConnection -ErrorAction Stop | Where-Object { $_.LocalPort -eq $Port -and $_.State -eq ''Listen'' })' + #13#10 +
    '}' + #13#10 +
    'function Stop-OwnerProcess([int]$ProcessId) {' + #13#10 +
    '  $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop' + #13#10 +
    '  if (-not $process) { throw "Process PID $ProcessId disappeared before ownership verification; refusing termination." }' + #13#10 +
    '  if (-not $process.ExecutablePath) { throw "Process PID $ProcessId has no executable path; refusing termination." }' + #13#10 +
    '  $full = Normalize-Path $process.ExecutablePath' + #13#10 +
    '  if (-not $full -or -not ($targets -icontains $full)) {' + #13#10 +
    '    throw "Refusing to terminate foreign process PID $ProcessId. ExecutablePath=$($process.ExecutablePath)"' + #13#10 +
    '  }' + #13#10 +
    '  if (-not (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) { return }' + #13#10 +
    '  Write-Host "Stopping Owner process PID $ProcessId ($($process.ExecutablePath))"' + #13#10 +
    '  $taskkill = Join-Path $env:SystemRoot ''System32\taskkill.exe''' + #13#10 +
    '  $killOutput = & $taskkill /PID $ProcessId /T /F 2>&1 | Out-String' + #13#10 +
    '  $killCode = $LASTEXITCODE' + #13#10 +
    '  Write-Host $killOutput.Trim()' + #13#10 +
    '  if ($killCode -ne 0 -and (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) {' + #13#10 +
    '    try { Stop-Process -Id $ProcessId -Force -ErrorAction Stop } catch {' + #13#10 +
    '      throw "Unable to terminate Owner PID $ProcessId. taskkill exit $killCode. $($_.Exception.Message)"' + #13#10 +
    '    }' + #13#10 +
    '  }' + #13#10 +
    '}' + #13#10 +
    'try {' + #13#10 +
    '  $running = @()' + #13#10 +
    '  for ($i = 0; $i -lt 20; $i++) {' + #13#10 +
    '    $running = @(Get-OwnerProcesses)' + #13#10 +
    '    if ($running.Count -eq 0) { break }' + #13#10 +
    '    Start-Sleep -Milliseconds 500' + #13#10 +
    '  }' + #13#10 +
    '  $running = @(Get-OwnerProcesses)' + #13#10 +
    '  foreach ($p in $running) { Stop-OwnerProcess -ProcessId $p.ProcessId }' + #13#10 +
    '  for ($i = 0; $i -lt 20; $i++) {' + #13#10 +
    '    $running = @(Get-OwnerProcesses)' + #13#10 +
    '    if ($running.Count -eq 0) { break }' + #13#10 +
    '    Start-Sleep -Milliseconds 250' + #13#10 +
    '  }' + #13#10 +
    '  $running = @(Get-OwnerProcesses)' + #13#10 +
    '  if ($running.Count -gt 0) {' + #13#10 +
    '    $details = ($running | ForEach-Object { "$($_.ProcessId):$($_.ExecutablePath)" }) -join '';''' + #13#10 +
    '    Write-Error "Owner process(es) remained alive after forced shutdown: $details"' + #13#10 +
    '    exit 11' + #13#10 +
    '  }' + #13#10 +
    '  $listeners = @()' + #13#10 +
    '  for ($i = 0; $i -lt 20; $i++) {' + #13#10 +
    '    $listeners = @(Get-OwnerListeners)' + #13#10 +
    '    if ($listeners.Count -eq 0) { break }' + #13#10 +
    '    Start-Sleep -Milliseconds 250' + #13#10 +
    '  }' + #13#10 +
    '  $listeners = @(Get-OwnerListeners)' + #13#10 +
    '  if ($listeners.Count -gt 0) {' + #13#10 +
    '    $listenerPids = ($listeners | ForEach-Object OwningProcess | Sort-Object -Unique) -join '',''' + #13#10 +
    '    foreach ($listenerPid in ($listeners | ForEach-Object OwningProcess | Sort-Object -Unique)) { Stop-OwnerProcess -ProcessId $listenerPid }' + #13#10 +
    '    Start-Sleep -Milliseconds 500' + #13#10 +
    '    $remaining = @(Get-OwnerListeners)' + #13#10 +
    '    if ($remaining.Count -gt 0) { Write-Error "Owner port $Port remained in LISTEN state. PID(s): $listenerPids"; exit 12 }' + #13#10 +
    '  }' + #13#10 +
    '  Start-Sleep -Milliseconds 500' + #13#10 +
    '  exit 0' + #13#10 +
    '} catch {' + #13#10 +
    '  Write-Error $_' + #13#10 +
    '  exit 20' + #13#10 +
    '}' + #13#10;

  if not SaveStringToFile(GuardPath, GuardScript, False) then
  begin
    Log('Could not create Owner runtime quiesce helper; refusing file replacement.');
    Result := False;
    Exit;
  end;

  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  Parameters := '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + GuardPath + '" -PythonTarget "' + PythonPath + '" -AppTarget "' + AppPath + '" -ServiceHostTarget "' + ServiceHostPath + '" -Port 8790';

  if not Exec(PowerShellExe, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Log('Could not launch Owner runtime quiesce helper; refusing file replacement.');
    Result := False;
    Exit;
  end;

  if ResultCode = 0 then
  begin
    Log('Owner runtime quiesced: desktop app, service host, bundled Python, and port 8790 are released.');
    Result := True;
    Exit;
  end;

  Log('Owner runtime quiesce helper failed with exit code ' + IntToStr(ResultCode) + '.');
  Result := False;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ScExe: String;
  QueryCode: Integer;
  StopCode: Integer;
  I: Integer;
  ServiceStopped: Boolean;
begin
  Result := '';
  ScExe := ExpandConstant('{sys}\sc.exe');
  ServiceStopped := False;

  Log('Checking Owner Friend Service before installer file replacement.');
  if not Exec(ScExe, 'query ResearchOSOwnerFriendService', '', SW_HIDE, ewWaitUntilTerminated, QueryCode) then
  begin
    Result := 'Failed to query ResearchOSOwnerFriendService before install/upgrade.';
    Exit;
  end;

  if QueryCode <> 0 then
  begin
    Log('ResearchOSOwnerFriendService is not registered; checking for orphaned Owner runtime processes.');
    ServiceStopped := True;
  end
  else if OwnerFriendServiceIsStopped() then
  begin
    Log('ResearchOSOwnerFriendService is already stopped; checking Owner runtime ownership.');
    ServiceStopped := True;
  end
  else
  begin
    Log('Stopping ResearchOSOwnerFriendService before installer file replacement.');
    if not Exec(ScExe, 'stop ResearchOSOwnerFriendService', '', SW_HIDE, ewWaitUntilTerminated, StopCode) then
    begin
      Result := 'Failed to launch service stop command for ResearchOSOwnerFriendService.';
      Exit;
    end;

    for I := 1 to 60 do
    begin
      if OwnerFriendServiceIsStopped() then
      begin
        Log('ResearchOSOwnerFriendService reached STOPPED state; quiescing bundled runtime.');
        ServiceStopped := True;
        Break;
      end;
      Sleep(500);
    end;

    if not ServiceStopped then
    begin
      Result := 'ResearchOSOwnerFriendService did not reach STOPPED state within 30 seconds. sc.exe stop exit code: ' + IntToStr(StopCode);
      Exit;
    end;
  end;

  if not QuiesceOwnerRuntime() then
  begin
    Result := 'Owner runtime could not be safely quiesced. Setup refused file replacement. See setup log for the quiesce helper exit code.';
    Exit;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then Log('Owner Special install/upgrade preserves ProgramData\ResearchOSOwnerSpecial.');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
    MsgBox('Research OS Owner Special was removed. Owner memory and provider configuration in ProgramData\ResearchOSOwnerSpecial were preserved.', mbInformation, MB_OK);
end;
