#define MyAppName "Research OS"
#define MyAppVersion "0.6.0"
#define MyAppPublisher "Research OS"
#define MyAppExeName "research_os_flutter.exe"

[Setup]
AppId={{9D9AC2C3-1C44-4EF0-9B04-4C8C47CF5338}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Research OS
DefaultGroupName=Research OS
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir=output
OutputBaseFilename=Research-OS-Setup-{#MyAppVersion}-x64
SetupIconFile=research-os.ico
UninstallDisplayName=Research OS
UninstallDisplayIcon={app}\app\{#MyAppExeName}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Research OS Windows Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion=0.6.0.6
SetupLogging=yes
ChangesEnvironment=yes

[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{commonappdata}\ResearchOS"
Name: "{commonappdata}\ResearchOS\database"
Name: "{commonappdata}\ResearchOS\sessions"
Name: "{commonappdata}\ResearchOS\artifacts"
Name: "{commonappdata}\ResearchOS\backups"
Name: "{commonappdata}\ResearchOS\logs"

[Icons]
Name: "{group}\Research OS"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"; IconFilename: "{app}\app\{#MyAppExeName}"
Name: "{autodesktop}\Research OS"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"; IconFilename: "{app}\app\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "startapp"; Description: "Launch Research OS after installation"; GroupDescription: "After setup:"; Flags: checkedonce

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-service.ps1"" -Action install -DataDir ""{commonappdata}\ResearchOS"""; StatusMsg: "Installing Research OS Windows Service..."; Flags: runhidden waituntilterminated
Filename: "{app}\app\{#MyAppExeName}"; Description: "Launch Research OS"; WorkingDir: "{app}\app"; Flags: nowait postinstall skipifsilent; Tasks: startapp

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-service.ps1"" -Action uninstall -DataDir ""{commonappdata}\ResearchOS"""; Flags: runhidden waituntilterminated; RunOnceId: "ResearchOSServiceUninstall"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    Log('Research OS installation completed. User data is stored under ProgramData\ResearchOS.');
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
  begin
    MsgBox('Research OS was removed. Your local Memory, sessions, backups and other data in ProgramData\ResearchOS were preserved.', mbInformation, MB_OK);
  end;
end;
