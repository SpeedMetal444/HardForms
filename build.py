"""
Script de compilación con PyInstaller
======================================
Uso:
    python build.py
"""
import os
import sys
import shutil

APP_NAME = "HardForms"
MAIN_SCRIPT = "main.py"
ICON_SRC = "resources/default_logo.png"
ICON_DST = "resources/icon.ico"

# Convertir PNG a ICO si no existe
if not os.path.isfile(ICON_DST) and os.path.isfile(ICON_SRC):
    try:
        from PIL import Image
        img = Image.open(ICON_SRC)
        img.save(ICON_DST, format="ICO", sizes=[(256, 256)])
        print(f"Ícono generado: {ICON_DST}")
    except ImportError:
        print("PIL no disponible, no se generó .ico")
    except Exception as e:
        print(f"Error generando .ico: {e}")

for d in ["build", "dist"]:
    if os.path.exists(d):
        shutil.rmtree(d)

os.makedirs("dist_temp/data", exist_ok=True)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--windowed", "--noconfirm",
    "--name", APP_NAME,
    "--add-data", f"config{os.pathsep}config",
    "--add-data", f"resources{os.pathsep}resources",
    "--add-data", f"database{os.pathsep}database",
    "--add-data", f"models{os.pathsep}models",
    "--add-data", f"reports{os.pathsep}reports",
    "--add-data", f"ui{os.pathsep}ui",
    "--add-data", f"data{os.pathsep}data",
]

if os.path.isfile(ICON_DST):
    cmd.extend(["--icon", ICON_DST])

cmd.append(MAIN_SCRIPT)

print(f"Ejecutando: {' '.join(cmd)}")
os.system(" ".join(cmd))

if os.path.isdir(f"dist/{APP_NAME}"):
    print(f"Compilación completa. Ejecutable en dist/{APP_NAME}/")
else:
    print("Error: no se generó el ejecutable.")
