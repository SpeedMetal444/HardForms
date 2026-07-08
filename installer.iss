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
ChangesEnvironment=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\HardForms\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\HardForms\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
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
  edtName, edtAddress, edtPhone, edtEmail, edtWeb, edtMP, edtDoctor: TEdit;
  lblLogo: TLabel;
  logoFile: string;

procedure BrowseLogo(Sender: TObject);
var
  f: string;
begin
  if GetOpenFileName('Seleccionar logo institucional', f,
     ExpandConstant('{src}'), 'Imágenes (*.png;*.jpg;*.bmp)|*.png;*.jpg;*.jpeg;*.bmp')
  then
  begin
    logoFile := f;
    lblLogo.Caption := 'Logo: ' + ExtractFileName(f);
  end;
end;

procedure InitializeWizard;
var
  lbl: TLabel;
  y: Integer;
  btn: TButton;
begin
  CustomPage := CreateCustomPage(wpSelectTasks, 'Configurar institución',
    'Ingresá los datos de la institución para el encabezado de los informes PDF.');

  y := 8;

  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Nombre de la institución:';
  lbl.Top := y;
  lbl.Left := 8;
  edtName := TEdit.Create(CustomPage);
  edtName.Parent := CustomPage.Surface;
  edtName.Top := y + 16;
  edtName.Left := 8;
  edtName.Width := 400;
  edtName.Text := 'Mi Centro Médico';

  y := edtName.Top + edtName.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Dirección:';
  lbl.Top := y;
  lbl.Left := 8;
  edtAddress := TEdit.Create(CustomPage);
  edtAddress.Parent := CustomPage.Surface;
  edtAddress.Top := y + 16;
  edtAddress.Left := 8;
  edtAddress.Width := 400;
  edtAddress.Text := 'Dirección del centro';

  y := edtAddress.Top + edtAddress.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Teléfono:';
  lbl.Top := y;
  lbl.Left := 8;
  edtPhone := TEdit.Create(CustomPage);
  edtPhone.Parent := CustomPage.Surface;
  edtPhone.Top := y + 16;
  edtPhone.Left := 8;
  edtPhone.Width := 400;
  edtPhone.Text := '+54 11 1234-5678';

  y := edtPhone.Top + edtPhone.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Email:';
  lbl.Top := y;
  lbl.Left := 8;
  edtEmail := TEdit.Create(CustomPage);
  edtEmail.Parent := CustomPage.Surface;
  edtEmail.Top := y + 16;
  edtEmail.Left := 8;
  edtEmail.Width := 400;
  edtEmail.Text := 'contacto@micentro.com';

  y := edtEmail.Top + edtEmail.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Sitio web:';
  lbl.Top := y;
  lbl.Left := 8;
  edtWeb := TEdit.Create(CustomPage);
  edtWeb.Parent := CustomPage.Surface;
  edtWeb.Top := y + 16;
  edtWeb.Left := 8;
  edtWeb.Width := 400;
  edtWeb.Text := 'www.micentro.com';

  y := edtWeb.Top + edtWeb.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Matrícula / MP:';
  lbl.Top := y;
  lbl.Left := 8;
  edtMP := TEdit.Create(CustomPage);
  edtMP.Parent := CustomPage.Surface;
  edtMP.Top := y + 16;
  edtMP.Left := 8;
  edtMP.Width := 400;
  edtMP.Text := 'MP 12345';

  y := edtMP.Top + edtMP.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Nombre del médico / director:';
  lbl.Top := y;
  lbl.Left := 8;
  edtDoctor := TEdit.Create(CustomPage);
  edtDoctor.Parent := CustomPage.Surface;
  edtDoctor.Top := y + 16;
  edtDoctor.Left := 8;
  edtDoctor.Width := 400;
  edtDoctor.Text := 'Juan Pérez';

  y := edtDoctor.Top + edtDoctor.Height + 8;
  lbl := TLabel.Create(CustomPage);
  lbl.Parent := CustomPage.Surface;
  lbl.Caption := 'Logo institucional (PNG recomendado):';
  lbl.Top := y;
  lbl.Left := 8;
  lblLogo := lbl;

  btn := TButton.Create(CustomPage);
  btn.Parent := CustomPage.Surface;
  btn.Top := y + 16;
  btn.Left := 8;
  btn.Width := 120;
  btn.Caption := 'Seleccionar...';
  btn.OnClick := @BrowseLogo;

  logoFile := '';
end;

procedure WriteInstitutionConfig(const AppDir: string);
var
  jsonPath, logoDest: string;
  jsonStr: string;
begin
  jsonPath := AddBackslash(AppDir) + 'data\institution_config.json';

  if (logoFile <> '') and FileExists(logoFile) then
  begin
    logoDest := AddBackslash(AppDir) + 'resources\custom_logo.png';
    FileCopy(logoFile, logoDest, False);
  end;

  jsonStr := '{' + #13#10 +
    '  "name": "' + edtName.Text + '",' + #13#10 +
    '  "address": "' + edtAddress.Text + '",' + #13#10 +
    '  "phone": "' + edtPhone.Text + '",' + #13#10 +
    '  "email": "' + edtEmail.Text + '",' + #13#10 +
    '  "web": "' + edtWeb.Text + '",' + #13#10 +
    '  "mp_number": "' + edtMP.Text + '",' + #13#10 +
    '  "doctor_name": "' + edtDoctor.Text + '",' + #13#10 +
    '  "logo_path": "' + logoDest + '",' + #13#10 +
    '  "footer_text": "Documento generado por HardForms © 2026"' + #13#10 +
    '}';

  SaveStringToFile(jsonPath, jsonStr, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    WriteInstitutionConfig(ExpandConstant('{app}'));
  end;
end;

function GetAppDir(Param: string): string;
begin
  Result := ExpandConstant('{app}');
end;
