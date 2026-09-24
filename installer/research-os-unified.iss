#define MyAppName "Research OS"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "Research OS Team"
#define MyAppExeName "research_os_flutter.exe"

[Setup]
AppId={{C6E8D8B0-2D6A-4B3D-8A7A-8A0F6B8A3E11}
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
OutputBaseFilename=Research-OS-Unified-Setup-{#MyAppVersion}-x64
UninstallDisplayName=Research OS
SetupLogging=yes
CloseApplications=yes
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
Name: "startapp"; Description: "Launch Research OS after setup"; GroupDescription: "After setup:"; Flags: checkedonce

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-service.ps1"" -Action install -DataDir ""{commonappdata}\ResearchOS"""; StatusMsg: "Installing Research OS Windows Service..."; Flags: runhidden waituntilterminated
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action install -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"" -ServiceName ""ResearchOSOwnerFriendService"" -OwnerId ""owner"" -Port 8790"; StatusMsg: "Installing Research OS Owner Friend Service..."; Flags: runhidden waituntilterminated
Filename: "{app}\app\{#MyAppExeName}"; Description: "Launch Research OS"; WorkingDir: "{app}\app"; Flags: nowait postinstall skipifsilent; Tasks: startapp

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action uninstall -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"" -ServiceName ""ResearchOSOwnerFriendService"" -Port 8790"; Flags: runhidden waituntilterminated
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-service.ps1"" -Action uninstall -DataDir ""{commonappdata}\ResearchOS"""; Flags: runhidden waituntilterminated
