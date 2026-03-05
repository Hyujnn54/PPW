; PPW Inno Setup Script
; Produces: PPW-Setup.exe
; Installs to: C:\Program Files\PPW
; Creates: Start Menu shortcut, Desktop shortcut, Uninstall entry

#define AppName "PPW Password Manager"
#define AppVersion "1.0.0"
#define AppPublisher "PPW"
#define AppURL "https://github.com/Hyujnn54/PPW"
#define AppExeName "PPW-PasswordManager.exe"
#define AppDescription "Secure password manager with cloud sync"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\PPW
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=PPW-Setup
SetupIconFile=extension\icons\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppDescription}
VersionInfoCompany={#AppPublisher}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

