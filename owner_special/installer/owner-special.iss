#define MyAppName "Research OS Owner Special"
#define MyAppVersion "1.3.0-owner"
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
OutputBaseFilename=Research-OS-Owner-Special-Setup-1.3.0-x64
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
  Result := Exec(
    CmdExe,
    '/C sc.exe query ResearchOSOwnerFriendService | findstr /C:"STOPPED" >nul',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode) and (ResultCode = 0);
end;

function QuiesceOwnerRuntime(): Boolean;
var
  ResultCode: Integer;
  PowerShellExe: String;
  PythonPath: String;
  GuardPath: String;
  GuardScript: String;
  Parameters: String;
begin
  PythonPath := ExpandConstant('{app}\runtime\python\python.exe');
  GuardPath := ExpandConstant('{tmp}\research-os-owner-runtime-quiesce.ps1');
  GuardScript :=
    'param([Parameter(Mandatory=$true)][string]$Target,[int]$Port=8790)' + #13#10 +
    '$ErrorActionPreference = ''Stop''' + #13#10 +
    'function Get-OwnerPython {' + #13#10 +
    '  $targetFull = [IO.Path]::GetFullPath($Target)' + #13#10 +
    '  return @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {' + #13#10 +
    '    $_.Name -ieq ''python.exe'' -and $_.ExecutablePath -and ([IO.Path]::GetFullPath($_.ExecutablePath) -ieq $targetFull)' + #13#10 +
    '  })' + #13#10 +
    '}' + #13#10 +
    'function Get-OwnerListeners {' + #13#10 +
    '  return @(Get-NetTCPConnection -ErrorAction Stop | Where-Object { $_.LocalPort -eq $Port -and $_.State -eq ''Listen'' })' + #13#10 +
    '}' + #13#10 +
    'try {' + #13#10 +
    '  $running = @()' + #13#10 +
    '  for ($i = 0; $i -lt 20; $i++) {' + #13#10 +
    '    $running = @(Get-OwnerPython)' + #13#10 +
    '    if ($running.Count -eq 0) { break }' + #13#10 +
    '    Start-Sleep -Milliseconds 500' + #13#10 +
    '  }' + #13#10 +
    '  $running = @(Get-OwnerPython)' + #13#10 +
    '  if ($running.Count -gt 0) {' + #13#10 +
    '    foreach ($p in $running) {' + #13#10 +
    '      Write-Host "Forcing bundled Owner Python PID $($p.ProcessId): $($p.ExecutablePath)"' + #13#10 +
    '      try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {' + #13#10 +
    '        if (Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue) { throw }' + #13#10 +
    '      }' + #13#10 +
    '    }' + #13#10 +
    '  }' + #13#10 +
    '  for ($i = 0; $i -lt 20; $i++) {' + #13#10 +
    '    $running = @(Get-OwnerPython)' + #13#10 +
    '    if ($running.Count -eq 0) { break }' + #13#10 +
    '    Start-Sleep -Milliseconds 250' + #13#10 +
    '  }' + #13#10 +
    '  $running = @(Get-OwnerPython)' + #13#10 +
    '  if ($running.Count -gt 0) {' + #13#10 +
    '    $pids = ($running | ForEach-Object ProcessId) -join '',''' + #13#10 +
    '    Write-Error "Bundled Owner Python remained alive after forced shutdown. PID(s): $pids"' + #13#10 +
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
    '    $pids = ($listeners | ForEach-Object OwningProcess | Sort-Object -Unique) -join '',''' + #13#10 +
    '    Write-Error "Owner port $Port remained in LISTEN state. PID(s): $pids"' + #13#10 +
    '    exit 12' + #13#10 +
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
  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + GuardPath +
    '" -Target "' + PythonPath + '" -Port 8790';

  if not Exec(
    PowerShellExe,
    Parameters,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode) then
  begin
    Log('Could not launch Owner runtime quiesce helper; refusing file replacement.');
    Result := False;
    Exit;
  end;

  if ResultCode = 0 then
  begin
    Log('Owner runtime quiesced: bundled Python is gone and port 8790 is released.');
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
    Result := 'Owner runtime could not be safely quiesced. Setup refused file replacement to prevent Access denied (code 5). See setup log for the quiesce helper exit code.';
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
