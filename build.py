"""
Compilar con PyInstaller → HardForms.exe (single‑file portable)
Uso: python build.py
"""
import os, sys, shutil

APP_NAME = "HardForms"
MAIN_SCRIPT = "main.py"
ICON_SRC = "resources/default_logo.png"
ICON_DST = "resources/icon.ico"

if not os.path.isfile(ICON_DST) and os.path.isfile(ICON_SRC):
    try:
        from PIL import Image
        Image.open(ICON_SRC).save(ICON_DST, format="ICO", sizes=[(256, 256)])
        print(f"Ícono: {ICON_DST}")
    except Exception as e:
        print(f"AVISO: no se generó .ico → {e}")

for d in ["build", "dist"]:
    shutil.rmtree(d, ignore_errors=True)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--windowed", "--noconfirm",
    "--onefile",
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

exe = os.path.join("dist", f"{APP_NAME}.exe")
if os.path.isfile(exe):
    sz = os.path.getsize(exe)
    print(f"✓ {exe}  ({sz / 1024 / 1024:.1f} MB)")
else:
    print("✗ Error: no se generó el ejecutable.")
