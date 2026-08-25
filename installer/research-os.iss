#define MyAppName "Research OS"
#define MyAppVersion "2.0.0-rc.1"
#define MyAppPublisher "Research OS"
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
UninstallDisplayName=Research OS
UninstallDisplayIcon={app}\app\{#MyAppExeName}
SetupLogging=yes
ChangesEnvironment=yes
CloseApplications=yes
RestartApplications=no

[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\v3\*"; DestDir: "{app}\v3"; Flags: ignoreversion recursesubdirs createallsubdirs

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
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-service.ps1"" -Action install -DataDir ""{commonappdata}\ResearchOS"""; StatusMsg: "Installing Research OS Windows Service..."; Flags: runhidden waituntilterminated
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action install -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"" -ServiceName ""ResearchOSOwnerFriendService"" -OwnerId ""owner"" -Port 8790"; StatusMsg: "Installing Research OS Owner Friend Service..."; Flags: runhidden waituntilterminated
Filename: "{app}\app\{#MyAppExeName}"; Description: "Launch Research OS"; WorkingDir: "{app}\app"; Flags: nowait postinstall skipifsilent; Tasks: startapp

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action uninstall -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"" -ServiceName ""ResearchOSOwnerFriendService"" -Port 8790"; Flags: runhidden waituntilterminated; RunOnceId: "ResearchOSOwnerFriendServiceUninstall"
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-service.ps1"" -Action uninstall -DataDir ""{commonappdata}\ResearchOS"""; Flags: runhidden waituntilterminated; RunOnceId: "ResearchOSServiceUninstall"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    Log('Research OS upgrade/install is preserving ProgramData\ResearchOS as the local data boundary.');
    Log('Research OS installation also installs the local Owner Friend Service on loopback port 8790.');
  end;
  if CurStep = ssPostInstall then
  begin
    Log('Research OS installation completed. User data is stored under ProgramData\ResearchOS.');
    Log('Owner Friend data is stored under ProgramData\ResearchOSOwnerSpecial.');
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
  begin
    MsgBox('Research OS was removed. Your local Memory, sessions, workspaces, backups and other data in ProgramData\ResearchOS and ResearchOSOwnerSpecial were preserved.', mbInformation, MB_OK);
  end;
end;
