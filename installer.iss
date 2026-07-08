; Script de Inno Setup para HardForms
; Requiere: PyInstaller build previo (python build.py)

#define MyAppName "HardForms"
#define MyAppVersion "1.0"
#define MyAppPublisher "HardForms"
#define MyAppURL "https://github.com/SpeedMetal444/HardForms"
#define MyAppExeName "HardForms.exe"

[Setup]
AppId={{B8A7C3D1-4E2F-4A6D-9F1C-8E5D3B2A7C0E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=HardForms_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\resources\icon.ico
WizardSizePercent=120

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "resources\default_logo.png"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "resources\default_logo_large.png"; DestDir: "{app}\resources"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent


