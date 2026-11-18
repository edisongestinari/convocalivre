; ConvocaLivre Windows installer — unsigned per-user setup.
; Compile from repository root after PyInstaller --onedir generated dist\ConvocaLivre.
#define MyAppName "ConvocaLivre"
#define MyAppVersion "0.6.1"
#define MyAppExeName "ConvocaLivre.exe"

[Setup]
AppId={{D9499EAA-AD3B-4A1F-8B01-8F8F44958EAE}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=ConvocaLivre contributors
AppPublisherURL=https://github.com/edisongestinari/convocalivre
AppSupportURL=https://github.com/edisongestinari/convocalivre/issues
AppUpdatesURL=https://github.com/edisongestinari/convocalivre/releases
DefaultDirName={localappdata}\Programs\ConvocaLivre
DefaultGroupName=ConvocaLivre
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist_installer
OutputBaseFilename=ConvocaLivre_Setup_0_6_1
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=..\LICENSE
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "..\dist\ConvocaLivre\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\ConvocaLivre"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\ConvocaLivre"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir ConvocaLivre"; Flags: nowait postinstall skipifsilent
