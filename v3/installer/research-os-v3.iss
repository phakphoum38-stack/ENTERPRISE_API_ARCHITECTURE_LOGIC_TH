#define MyAppName "Research OS 3.2 Unified"
#define MyAppVersion "3.2.0-unified"
#define MyAppPublisher "Research OS Team"
#define MyAppExeName "research_os_v3_flutter.exe"

[Setup]
AppId={{4F563352-434C-4541-4E52-455345415243}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Research OS 3.2 Unified
DefaultGroupName=Research OS 3.2 Unified
UsePreviousAppDir=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir=output
OutputBaseFilename=Research-OS-3.2-Unified-Setup-x64
SetupIconFile=research_os_v3.ico
UninstallDisplayName=Research OS 3.2 Unified
UninstallDisplayIcon={app}\app\{#MyAppExeName}
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{commonappdata}\ResearchOSV3"
Name: "{commonappdata}\ResearchOSV3\sessions"
Name: "{commonappdata}\ResearchOSV3\database"
Name: "{commonappdata}\ResearchOSV3\artifacts"
Name: "{commonappdata}\ResearchOSV3\logs"
Name: "{commonappdata}\ResearchOSV3\evidence"

[Icons]
Name: "{group}\Research OS 3.2 Unified"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"
Name: "{autodesktop}\Research OS 3.2 Unified"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "startapp"; Description: "Launch Research OS 3.2 Unified after installation"; GroupDescription: "After setup:"; Flags: checkedonce

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\v3-service.ps1"" -Action install"; StatusMsg: "Installing Research OS V3 unified local service..."; Flags: runhidden waituntilterminated
Filename: "{app}\app\{#MyAppExeName}"; Description: "Launch Research OS 3.2 Unified"; WorkingDir: "{app}\app"; Flags: nowait postinstall skipifsilent; Tasks: startapp

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\v3-service.ps1"" -Action uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "ResearchOSV3ServiceUninstall"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  ScriptPath: String;
  PowerShellPath: String;
  Parameters: String;
begin
  Result := '';
  ScriptPath := ExpandConstant('{app}\scripts\v3-service.ps1');
  if FileExists(ScriptPath) then
  begin
    PowerShellPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
    Parameters := '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + ScriptPath + '" -Action uninstall';
    if not Exec(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      Result := 'Unable to stop the existing Research OS V3 service before upgrade.'
    else if ResultCode <> 0 then
      Result := 'The existing Research OS V3 service could not be stopped cleanly before upgrade.';
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    Log('Research OS 3.2 Unified install/upgrade preserves ProgramData\ResearchOSV3.');
  if CurStep = ssPostInstall then
    Log('Research OS 3.2 Unified installation completed.');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
    MsgBox('Research OS 3.2 Unified was removed. Local data under ProgramData\ResearchOSV3 was preserved.', mbInformation, MB_OK);
end;
