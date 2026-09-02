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
Source: "scripts\research-os-owner-runtime-quiesce.ps1"; Flags: dontcopy

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
  QuiesceLogPath: String;
  Parameters: String;
begin
  Result := False;

  PythonPath := ExpandConstant('{app}\runtime\python\python.exe');
  AppPath := ExpandConstant('{app}\app\{#MyAppExeName}');
  ServiceHostPath :=
    ExpandConstant('{app}\service_host\ResearchOS.Owner.ServiceHost.exe');

  GuardPath :=
    ExpandConstant('{tmp}\research-os-owner-runtime-quiesce.ps1');
  QuiesceLogPath :=
    ExpandConstant('{%TEMP}') + '\ResearchOS-Owner-Quiesce.log';

  Log('Extracting Owner runtime quiesce helper.');
  Log('Owner quiesce diagnostic log: ' + QuiesceLogPath);

  ExtractTemporaryFile('research-os-owner-runtime-quiesce.ps1');

  if not FileExists(GuardPath) then
  begin
    Log('Could not extract Owner runtime quiesce helper; refusing file replacement.');
    Result := False;
    Exit;
  end;

  PowerShellExe :=
    ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');

  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass ' +
    '-File "' + GuardPath + '"' +
    ' -PythonTarget "' + PythonPath + '"' +
    ' -AppTarget "' + AppPath + '"' +
    ' -ServiceHostTarget "' + ServiceHostPath + '"' +
    ' -Port 8790' +
    ' -LogPath "' + QuiesceLogPath + '"';

  Log('Launching Owner runtime quiesce helper.');

  if not Exec(
    PowerShellExe,
    Parameters,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    Log('Could not launch Owner runtime quiesce helper; refusing file replacement.');
    Exit;
  end;

  Log('Owner runtime quiesce helper exit code: ' + IntToStr(ResultCode));
  Log('Owner quiesce diagnostic log remains at: ' + QuiesceLogPath);

  if ResultCode = 0 then
  begin
    Log('Owner runtime quiesced: desktop app, service host, bundled Python, and port 8790 are released.');
    Result := True;
    Exit;
  end;

  Log(
    'Owner runtime quiesce helper failed with exit code ' +
    IntToStr(ResultCode) +
    '. Detailed diagnostic: ' +
    QuiesceLogPath
  );

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
    Result := 'Owner runtime could not be safely quiesced. Setup refused file replacement. See setup log and the detailed quiesce diagnostic log path recorded there.';
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
