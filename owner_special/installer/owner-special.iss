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
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  PowerShellExe: String;
  Parameters: String;
  ResultCode: Integer;
begin
  Result := '';
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    '$service = Get-Service -Name ''ResearchOSOwnerFriendService'' -ErrorAction SilentlyContinue; ' +
    'if ($null -ne $service -and $service.Status -ne ''Stopped'') { ' +
    'Write-Host ''Stopping ResearchOSOwnerFriendService before file replacement...''; ' +
    'Stop-Service -Name ''ResearchOSOwnerFriendService'' -Force -ErrorAction Stop; ' +
    '$service = Get-Service -Name ''ResearchOSOwnerFriendService'' -ErrorAction Stop; ' +
    '$service.WaitForStatus(''Stopped'', [TimeSpan]::FromSeconds(30)); ' +
    '$service.Refresh(); ' +
    'if ($service.Status -ne ''Stopped'') { exit 12 }; ' +
    '}"';

  Log('Stopping Owner Friend Service before installer file replacement when upgrading.');
  if not Exec(PowerShellExe, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Result := 'Failed to launch PowerShell while preparing the Owner Friend Service for install/upgrade.';
    Exit;
  end;

  if ResultCode <> 0 then
  begin
    Result := 'Could not stop ResearchOSOwnerFriendService before installer file replacement. PowerShell exit code: ' + IntToStr(ResultCode);
    Exit;
  end;

  Log('Owner Friend Service is stopped or was not installed; file replacement may proceed.');
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
