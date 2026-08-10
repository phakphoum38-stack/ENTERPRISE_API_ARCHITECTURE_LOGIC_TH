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

function OwnerBundledPythonHasExited(): Boolean;
var
  ResultCode: Integer;
  PowerShellExe: String;
  PythonPath: String;
  EscapedPythonPath: String;
  CommandLine: String;
begin
  PythonPath := ExpandConstant('{app}\runtime\python\python.exe');
  if not FileExists(PythonPath) then
  begin
    Result := True;
    Exit;
  end;

  EscapedPythonPath := StringChangeEx(PythonPath, '''', '''''', True);
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  CommandLine :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    '$target=[IO.Path]::GetFullPath(''''' + EscapedPythonPath + '''''); ' +
    '$running=@(Get-CimInstance Win32_Process -Filter ''''Name = ''''''python.exe'''''''''''' | ' +
    'Where-Object { $_.ExecutablePath -and ([IO.Path]::GetFullPath($_.ExecutablePath) -ieq $target) }); ' +
    'if ($running.Count -eq 0) { exit 0 } else { exit 10 }"';

  if not Exec(
    PowerShellExe,
    CommandLine,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode) then
  begin
    Log('Could not launch bundled Python ownership check; refusing file replacement until runtime ownership is proven clear.');
    Result := False;
    Exit;
  end;

  if (ResultCode <> 0) and (ResultCode <> 10) then
    Log('Bundled Python ownership check returned unexpected exit code ' + IntToStr(ResultCode) + '.');
  Result := ResultCode = 0;
end;

function WaitForOwnerBundledPythonExit(): Boolean;
var
  I: Integer;
begin
  for I := 1 to 60 do
  begin
    if OwnerBundledPythonHasExited() then
    begin
      Log('Bundled Owner Python runtime is no longer running; file replacement may proceed.');
      Result := True;
      Exit;
    end;
    Sleep(500);
  end;

  Log('Bundled Owner Python runtime remained active after 30 seconds.');
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
    Log('ResearchOSOwnerFriendService is not registered; checking for any orphaned bundled Python runtime before file replacement.');
    ServiceStopped := True;
  end
  else if OwnerFriendServiceIsStopped() then
  begin
    Log('ResearchOSOwnerFriendService is already stopped; checking bundled Python runtime ownership before file replacement.');
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
        Log('ResearchOSOwnerFriendService reached STOPPED state; waiting for bundled Python runtime to exit.');
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

  if not WaitForOwnerBundledPythonExit() then
  begin
    Result := 'ResearchOSOwnerFriendService is stopped, but the bundled runtime\python\python.exe process is still active after 30 seconds. Upgrade was stopped to prevent Access denied (code 5) during file replacement.';
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
