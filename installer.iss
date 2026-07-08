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

procedure InitializeWizard;
var
  OuterBox: TScrollBox;
  lbl: TLabel;
begin
  CustomPage := CreateCustomPage(wpSelectTasks, 'Configurar institución',
    'Ingresá los datos de la institución para el encabezado de los informes PDF.');

  OuterBox := TScrollBox.Create(CustomPage);
  OuterBox.Parent := CustomPage.Surface;
  OuterBox.Align := alClient;
  OuterBox.VertScrollBar.Visible := True;

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Nombre de la institución:';
  lbl.Top := 8;
  lbl.Left := 8;
  edtName := TEdit.Create(OuterBox);
  edtName.Parent := OuterBox;
  edtName.Top := lbl.Top + lbl.Height + 2;
  edtName.Left := 8;
  edtName.Width := 400;
  edtName.Text := 'Mi Centro Médico';

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Dirección:';
  lbl.Top := edtName.Top + edtName.Height + 8;
  lbl.Left := 8;
  edtAddress := TEdit.Create(OuterBox);
  edtAddress.Parent := OuterBox;
  edtAddress.Top := lbl.Top + lbl.Height + 2;
  edtAddress.Left := 8;
  edtAddress.Width := 400;
  edtAddress.Text := 'Dirección del centro';

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Teléfono:';
  lbl.Top := edtAddress.Top + edtAddress.Height + 8;
  lbl.Left := 8;
  edtPhone := TEdit.Create(OuterBox);
  edtPhone.Parent := OuterBox;
  edtPhone.Top := lbl.Top + lbl.Height + 2;
  edtPhone.Left := 8;
  edtPhone.Width := 400;
  edtPhone.Text := '+54 11 1234-5678';

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Email:';
  lbl.Top := edtPhone.Top + edtPhone.Height + 8;
  lbl.Left := 8;
  edtEmail := TEdit.Create(OuterBox);
  edtEmail.Parent := OuterBox;
  edtEmail.Top := lbl.Top + lbl.Height + 2;
  edtEmail.Left := 8;
  edtEmail.Width := 400;
  edtEmail.Text := 'contacto@micentro.com';

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Sitio web:';
  lbl.Top := edtEmail.Top + edtEmail.Height + 8;
  lbl.Left := 8;
  edtWeb := TEdit.Create(OuterBox);
  edtWeb.Parent := OuterBox;
  edtWeb.Top := lbl.Top + lbl.Height + 2;
  edtWeb.Left := 8;
  edtWeb.Width := 400;
  edtWeb.Text := 'www.micentro.com';

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Matrícula / MP:';
  lbl.Top := edtWeb.Top + edtWeb.Height + 8;
  lbl.Left := 8;
  edtMP := TEdit.Create(OuterBox);
  edtMP.Parent := OuterBox;
  edtMP.Top := lbl.Top + lbl.Height + 2;
  edtMP.Left := 8;
  edtMP.Width := 400;
  edtMP.Text := 'MP 12345';

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Nombre del médico / director:';
  lbl.Top := edtMP.Top + edtMP.Height + 8;
  lbl.Left := 8;
  edtDoctor := TEdit.Create(OuterBox);
  edtDoctor.Parent := OuterBox;
  edtDoctor.Top := lbl.Top + lbl.Height + 2;
  edtDoctor.Left := 8;
  edtDoctor.Width := 400;
  edtDoctor.Text := 'Juan Pérez';

  lbl := TLabel.Create(OuterBox);
  lbl.Parent := OuterBox;
  lbl.Caption := 'Logo institucional (PNG recomendado):';
  lbl.Top := edtDoctor.Top + edtDoctor.Height + 8;
  lbl.Left := 8;
  lblLogo := lbl;

  logoFile := '';
end;

procedure BrowseLogo(Sender: TObject);
var
  fd: TOpenDialog;
begin
  fd := TOpenDialog.Create(nil);
  fd.Filter := 'Imágenes|*.png;*.jpg;*.jpeg;*.bmp|Todos los archivos|*.*';
  fd.Title := 'Seleccionar logo institucional';
  if fd.Execute then
  begin
    logoFile := fd.FileName;
    lblLogo.Caption := 'Logo: ' + ExtractFileName(logoFile);
  end;
  fd.Free;
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
