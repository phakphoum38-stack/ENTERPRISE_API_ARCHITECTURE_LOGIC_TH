#define MyAppName "Research OS"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "Research OS Team"
#define MyAppExeName "research_os_flutter.exe"

#ifndef PlatformZip
#error "PlatformZip must be supplied by the canonical Platform distribution workflow."
#endif
#ifndef PlatformZipSha256
#error "PlatformZipSha256 must be supplied by the canonical Platform distribution workflow."
#endif
#ifndef PlatformSourceSha
#error "PlatformSourceSha must be supplied by the canonical Platform distribution workflow."
#endif
#ifndef PlatformZipName
#error "PlatformZipName must be supplied by the canonical Platform distribution workflow."
#endif

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
WizardStyle=modern dynamic windows11 hidebevels includetitlebar
SetupIconFile=..\..\assets\branding\research_os.ico
UninstallDisplayIcon={app}\app\{#MyAppExeName}
OutputDir=output
OutputBaseFilename=Research-OS-Owner-Special-Setup-{#MyAppVersion}-x64
UninstallDisplayName=Research OS
SetupLogging=yes
CloseApplications=yes
RestartApplications=no
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoDescription=Research OS Platform installer
VersionInfoOriginalFileName=Research-OS-Owner-Special-Setup-{#MyAppVersion}-x64.exe

[Files]
Source: "{#PlatformZip}"; DestDir: "{app}"; Flags: ignoreversion
Source: "install-platform-zip.ps1"; DestDir: "{app}"; Flags: ignoreversion

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
Filename: "{app}\app\{#MyAppExeName}"; Description: "Launch Research OS"; WorkingDir: "{app}\app"; Flags: nowait postinstall skipifsilent; Tasks: startapp

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\owner_special\scripts\install-owner-service.ps1"" -Action uninstall -Root ""{app}"" -DataDir ""{commonappdata}\ResearchOSOwnerSpecial"" -ServiceName ""ResearchOSOwnerFriendService"" -Port 8790"; Flags: runhidden waituntilterminated
Filename: "powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{app}\scripts\research-os-service.ps1"" -Action uninstall -DataDir ""{commonappdata}\ResearchOS"""; Flags: runhidden waituntilterminated

[UninstallDelete]
Type: filesandordirs; Name: "{app}\*"

[Code]
procedure LogDiagnosticFile(const FileName: String);
var
  Contents: AnsiString;
  Line: String;
  NewLinePos: Integer;
begin
  if not FileExists(FileName) then
  begin
    Log('Platform bootstrap diagnostic file not found: ' + FileName);
    Exit;
  end;
  if not LoadStringFromFile(FileName, Contents) then
  begin
    Log('Unable to read platform bootstrap diagnostic file: ' + FileName);
    Exit;
  end;
  Log('--- Research OS Platform bootstrap diagnostics ---');
  while Contents <> '' do
  begin
    NewLinePos := Pos(#10, Contents);
    if NewLinePos = 0 then
    begin
      Line := String(Contents);
      Contents := '';
    end
    else
    begin
      Line := Copy(Contents, 1, NewLinePos - 1);
      Delete(Contents, 1, NewLinePos);
    end;
    if (Line <> '') and (Line[Length(Line)] = #13) then
      Delete(Line, Length(Line), 1);
    if Line <> '' then Log(Line);
  end;
  Log('--- End Research OS Platform bootstrap diagnostics ---');
end;

function RunPowerShellChecked(const Description, Parameters: String): Boolean;
var
  ResultCode: Integer;
  PowerShellExe: String;
begin
  Result := False;
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  Log(Description);
  Log('PowerShell: ' + PowerShellExe);
  Log('Parameters: ' + Parameters);
  if not Exec(PowerShellExe, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then Exit;
  Log(Description + ' exit code: ' + IntToStr(ResultCode));
  Result := ResultCode = 0;
end;

function InstallCanonicalPlatform(): Boolean;
var
  ZipPath, TargetRoot, Parameters, DiagnosticLogPath: String;
begin
  Result := False;
  TargetRoot := ExpandConstant('{app}');
  DiagnosticLogPath := ExpandConstant('{tmp}\ResearchOS-Platform-install.log');
  ZipPath := AddBackslash(TargetRoot) + '{#PlatformZipName}';
  Log('Canonical Platform ZIP payload path: ' + ZipPath);
  if not FileExists(ZipPath) then
  begin
    Log('Canonical Platform ZIP missing from Setup payload: ' + ZipPath);
    Exit;
  end;
  Log('Canonical Platform ZIP payload exists. Size=' + IntToStr(GetFileSize(ZipPath)) + ' bytes');
  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
    AddBackslash(TargetRoot) + 'install-platform-zip.ps1" ' +
    '-ZipPath "' + ZipPath + '" ' +
    '-TargetRoot "' + TargetRoot + '" ' +
    '-ExpectedZipSha256 "{#PlatformZipSha256}" ' +
    '-ExpectedSourceSha "{#PlatformSourceSha}" ' +
    '-DiagnosticLogPath "' + DiagnosticLogPath + '"';
  if not RunPowerShellChecked('Installing Research OS Platform from canonical ZIP', Parameters) then
  begin
    LogDiagnosticFile(DiagnosticLogPath);
    Exit;
  end;
  Result := True;
end;

function InstallResearchOsService(): Boolean;
var Parameters: String;
begin
  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{app}\scripts\research-os-service.ps1') +
    '" -Action install -DataDir "' + ExpandConstant('{commonappdata}\ResearchOS') + '"';
  Result := RunPowerShellChecked('Installing Research OS Windows Service', Parameters);
end;

function InstallOwnerFriendService(): Boolean;
var Parameters: String;
begin
  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{app}\owner_special\scripts\install-owner-service.ps1') +
    '" -Action install -Root "' + ExpandConstant('{app}') +
    '" -DataDir "' + ExpandConstant('{commonappdata}\ResearchOSOwnerSpecial') +
    '" -ServiceName "ResearchOSOwnerFriendService" -OwnerId "owner" -Port 8790';
  Result := RunPowerShellChecked('Installing Research OS Owner Friend Service', Parameters);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    Log('Owner Special Setup is the Platform installation entry point.');
    Log('Installer UI identity: canonical Research OS Platform.');
    Log('Installation payload: canonical Research OS Platform ZIP.');
    if not InstallCanonicalPlatform() then begin
      MsgBox('Research OS Platform installation failed. Setup will stop.', mbCriticalError, MB_OK);
      Abort;
    end;
    if not InstallResearchOsService() then begin
      MsgBox('Research OS Windows Service installation failed. Setup will stop.', mbCriticalError, MB_OK);
      Abort;
    end;
    if not InstallOwnerFriendService() then begin
      MsgBox('Research OS Owner Friend Service installation failed. Setup will stop.', mbCriticalError, MB_OK);
      Abort;
    end;
  end;
end;
