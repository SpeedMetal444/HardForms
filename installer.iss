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

[Code]
var
  CustomPage: TWizardPage;
  edtName, edtAddress, edtPhone, edtDoctor: TEdit;

procedure InitializeWizard;
var
  lbl: TLabel;
  y: Integer;
begin
  CustomPage := CreateCustomPage(wpSelectTasks, 'Configurar institución',
    'Completá los datos de la institución (podés cambiarlos después desde Herramientas → Configurar institución).');

  y := 8;

  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Nombre de la institución:';
  lbl.Top := y; lbl.Left := 8;
  edtName := TEdit.Create(CustomPage);
  edtName.Parent := CustomPage.Surface;
  edtName.Top := y + 16; edtName.Left := 8; edtName.Width := 400;
  edtName.Text := 'Mi Centro Médico';

  y := edtName.Top + edtName.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Dirección:';
  lbl.Top := y; lbl.Left := 8;
  edtAddress := TEdit.Create(CustomPage);
  edtAddress.Parent := CustomPage.Surface;
  edtAddress.Top := y + 16; edtAddress.Left := 8; edtAddress.Width := 400;

  y := edtAddress.Top + edtAddress.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Teléfono:';
  lbl.Top := y; lbl.Left := 8;
  edtPhone := TEdit.Create(CustomPage);
  edtPhone.Parent := CustomPage.Surface;
  edtPhone.Top := y + 16; edtPhone.Left := 8; edtPhone.Width := 400;

  y := edtPhone.Top + edtPhone.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Nombre del médico / director:';
  lbl.Top := y; lbl.Left := 8;
  edtDoctor := TEdit.Create(CustomPage);
  edtDoctor.Parent := CustomPage.Surface;
  edtDoctor.Top := y + 16; edtDoctor.Left := 8; edtDoctor.Width := 400;
end;

procedure WriteInstitutionConfig(const AppDir: string);
var
  dataDir: string;
  jsonPath: string;
  jsonStr: string;
begin
  dataDir := AddBackslash(AppDir) + 'data';
  if not DirExists(dataDir) then
    CreateDir(dataDir);
  jsonPath := dataDir + '\institution_config.json';

  jsonStr := '{' + #13#10 +
    '  "name": "' + edtName.Text + '",' + #13#10 +
    '  "address": "' + edtAddress.Text + '",' + #13#10 +
    '  "phone": "' + edtPhone.Text + '",' + #13#10 +
    '  "email": "",' + #13#10 +
    '  "web": "",' + #13#10 +
    '  "mp_number": "",' + #13#10 +
    '  "doctor_name": "' + edtDoctor.Text + '",' + #13#10 +
    '  "logo_path": "",' + #13#10 +
    '  "watermark_path": "",' + #13#10 +
    '  "default_logo": "resources\\default_logo.png",' + #13#10 +
    '  "footer_text": "Documento generado por HardForms © 2026"' + #13#10 +
    '}';

  SaveStringToFile(jsonPath, jsonStr, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  configPath: string;
begin
  if CurStep = ssPostInstall then
  begin
    WriteInstitutionConfig(ExpandConstant('{app}'));
    configPath := ExpandConstant('{app}') + '\data\institution_config.json';
    if not FileExists(configPath) then
      MsgBox('ERROR: No se pudo crear el archivo de configuración en:'#13 +
        configPath, mbError, MB_OK);
    MsgBox('HardForms instalado correctamente.'#13#13 +
      'Para agregar imágenes a los pacientes, usá los botones'#13 +
      '"Agregar imagen" en la ventana de edición del paciente.'#13#13 +
      'Podés cambiar el logo y más datos desde:'#13 +
      '  Herramientas → Configurar institución'#13#13 +
      'Los datos se guardan automáticamente en:'#13 +
      '  ' + ExpandConstant('{app}') + '\data'#13 +
      'Hacé backups periódicos desde:'#13 +
      '  Herramientas → Backup'#13 +
      '¡Gracias por usar HardForms!',
      mbInformation, MB_OK);
  end;
end;
