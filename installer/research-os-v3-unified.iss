#define MyAppName "Research OS"
#define MyAppVersion "3.0.0-10x10"
#define MyAppPublisher "Research OS Team"
#define MyAppExeName "research_os_flutter.exe"

[Setup]
AppId={{9D9AC2C3-1C44-4EF0-9B04-4C8C47CF5338}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Research OS
DefaultGroupName=Research OS
UsePreviousAppDir=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir=output
OutputBaseFilename=Research-OS-Setup-{#MyAppVersion}-x64
SetupIconFile=..\apps\research_os_flutter\assets\branding\research_os.ico
UninstallDisplayName=Research OS
UninstallDisplayIcon={app}\app\{#MyAppExeName}
SetupLogging=yes
ChangesEnvironment=yes
CloseApplications=yes
CloseApplicationsFilter=research_os_flutter.exe
RestartApplications=no

[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{commonappdata}\ResearchOS"
Name: "{commonappdata}\ResearchOS\database"
Name: "{commonappdata}\ResearchOS\sessions"
Name: "{commonappdata}\ResearchOS\artifacts"
Name: "{commonappdata}\ResearchOS\backups"
Name: "{commonappdata}\ResearchOS\logs"
Name: "{commonappdata}\ResearchOS\workspaces"
Name: "{commonappdata}\ResearchOSOwnerSpecial"

[Icons]
Name: "{group}\Research OS"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"
Name: "{autodesktop}\Research OS"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "startapp"; Description: "Launch Research OS after installation"; GroupDescription: "After setup:"; Flags: checkedonce

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action install -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"""; StatusMsg: "Starting Research OS Friend / V3 10^10 service..."; Flags: runhidden waituntilterminated logoutput
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-unified-service.ps1"" -Action install -DataDir ""{commonappdata}\ResearchOS"""; StatusMsg: "Starting Research OS local API service..."; Flags: runhidden waituntilterminated logoutput
Filename: "{app}\app\{#MyAppExeName}"; Description: "Launch Research OS"; WorkingDir: "{app}\app"; Flags: nowait postinstall skipifsilent; Tasks: startapp

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-unified-service.ps1"" -Action uninstall -DataDir ""{commonappdata}\ResearchOS"""; Flags: runhidden waituntilterminated logoutput; RunOnceId: "ResearchOSServiceUninstall"
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action uninstall -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"""; Flags: runhidden waituntilterminated logoutput; RunOnceId: "ResearchOSOwnerFriendServiceUninstall"

[Code]
function StopExistingService(const ScriptPath, Parameters, FailureMessage: String): String;
var
  ResultCode: Integer;
  PowerShellPath: String;
begin
  Result := '';
  if not FileExists(ScriptPath) then
    exit;

  PowerShellPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  if not Exec(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := FailureMessage
  else if ResultCode <> 0 then
    Result := FailureMessage + ' PowerShell exit code: ' + IntToStr(ResultCode);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  MainScript: String;
  FriendScript: String;
  ErrorText: String;
begin
  Result := '';

  MainScript := ExpandConstant('{app}\scripts\research-os-unified-service.ps1');
  ErrorText := StopExistingService(
    MainScript,
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + MainScript + '" -Action uninstall -DataDir "' + ExpandConstant('{commonappdata}\ResearchOS') + '"',
    'Could not stop the existing Research OS service before upgrade.'
  );
  if ErrorText <> '' then
  begin
    Result := ErrorText;
    exit;
  end;

  FriendScript := ExpandConstant('{app}\owner_special\scripts\install-owner-service.ps1');
  ErrorText := StopExistingService(
    FriendScript,
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + FriendScript + '" -Action uninstall -Root "' + ExpandConstant('{app}') + '" -DataDir "' + ExpandConstant('{commonappdata}\ResearchOSOwnerSpecial') + '"',
    'Could not stop the existing Research OS Friend service before upgrade.'
  );
  if ErrorText <> '' then
  begin
    Result := ErrorText;
    exit;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    Log('Research OS 3.0 10x10 upgrade preserves ProgramData data boundaries and replaces application/runtime files only.');
  if CurStep = ssPostInstall then
    Log('Research OS 3.0 10x10 unified installation completed: GUI + Main API + Friend + V3.');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
    MsgBox('Research OS was removed. Local data under ProgramData\ResearchOS and ProgramData\ResearchOSOwnerSpecial was preserved.', mbInformation, MB_OK);
end;
