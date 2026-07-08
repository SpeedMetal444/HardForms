# HardForms

Aplicación de escritorio para gestión de pacientes, estudios y diagnósticos médicos. Desarrollada en Python con PyQt6.

## Funcionalidades

- **Pacientes**: alta, edición, visualización y eliminación con búsqueda por nombre, apellido o HC.
- **Estudios**: carga de informes, imágenes adjuntas (JPG/PNG), tipo de anestesia (Local/General), drogas, escala de Boston.
- **Diagnósticos**: múltiples diagnósticos por paciente con fecha.
- **PDF**: generación de informes con logo institucional, datos del paciente, imágenes en grilla compacta, secciones con encabezados azules.
- **Importación**: desde archivos `.mdb` (Access 97 vía VBScript de 32 bits) y `.csv`.
- **Exportación**: a `.csv` con imágenes incluidas.
- **Backup / Restore**: comprimido ZIP con base de datos e imágenes.
- **Configurable**: nombre, dirección, teléfono, email, web, matrícula, médico director, logo y pie de página desde el menú *Herramientas → Configurar institución*.

## Requisitos para desarrollo

- Python 3.10+
- Dependencias: `pip install -r requirements.txt`

## Compilar ejecutable

```bash
python build.py
```

Genera `dist/HardForms.exe` (single‑file portable, ~50 MB).

## Instalador

Usando Inno Setup 6:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Genera `installer/HardForms_Setup.exe`.

## Ejecutar desde código

```bash
python main.py
```

## Estructura del proyecto

```
HardForms/
├── main.py                      # Punto de entrada
├── build.py                     # Script de compilación PyInstaller
├── installer.iss                # Script de Inno Setup
├── requirements.txt             # Dependencias
├── config/
│   └── institution.py           # Configuración dinámica de la institución
├── database/
│   └── db.py                    # SQLite: esquema, migraciones, CRUD
├── models/
│   ├── patient.py               # Dataclasses Patient e ImageAttachment
│   └── diagnosis.py             # Dataclass Diagnosis
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # Ventana principal con tabla y menús
│   ├── patient_dialog.py        # Diálogo de alta/edición de paciente
│   ├── patient_view.py          # Vista detalle del paciente
│   ├── setup_dialog.py          # Configuración de institución
│   └── widgets.py               # Componentes reutilizables (DateMaskEdit, DateItem)
├── reports/
│   └── pdf_generator.py         # Generación de PDF con ReportLab
├── importer.py                  # Importación desde MDB a SQLite
├── export_table.vbs             # VBScript de 32 bits para exportar tablas Access
├── resources/
│   ├── default_logo.png         # Logo institucional por defecto
│   └── default_logo_large.png   # Versión grande del logo
└── data/
    └── institution_config.json  # Configuración de la institución (trackeada)
```

## Notas

- El número de historia clínica es auto‑incremental con formato `HC-00001`.
- La base de datos SQLite se crea automáticamente en `data/patients.db` al iniciar.
- Para importar archivos `.mdb` se necesita el driver Microsoft Jet OLEDB 4.0 (incluido en Windows de 32 bits o vía SysWOW64 en 64 bits).
- El logo por defecto puede reemplazarse desde *Herramientas → Configurar institución*.
