"""
Script de compilación con PyInstaller
======================================
Antes de compilar, personalizá config/institution.py
con los datos y logo de la institución.

Uso:
    python build.py
"""
import os
import sys
import shutil

# --- Configuración ---
APP_NAME = "HardForms"
MAIN_SCRIPT = "main.py"
ICON_PATH = "resources/icon.ico"  # opcional

# --- Clean previous builds ---
for d in ["build", "dist"]:
    if os.path.exists(d):
        shutil.rmtree(d)

# --- Build command ---
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--windowed",
    "--name", APP_NAME,
    "--add-data", f"config{os.pathsep}config",
    "--add-data", f"resources{os.pathsep}resources",
    "--add-data", f"database{os.pathsep}database",
    "--add-data", f"models{os.pathsep}models",
    "--add-data", f"reports{os.pathsep}reports",
    "--add-data", f"ui{os.pathsep}ui",
    "--noconfirm",
]

if os.path.isfile(ICON_PATH):
    cmd.extend(["--icon", ICON_PATH])

cmd.append(MAIN_SCRIPT)

print(f"Ejecutando: {' '.join(cmd)}")
os.system(" ".join(cmd))

print(f"\nCompilación completa. Ejecutable en dist/{APP_NAME}/")
