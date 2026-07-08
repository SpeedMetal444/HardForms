"""
CONFIGURACIÓN DE LA INSTITUCIÓN
================================
Personalizá estos valores desde el menú Herramientas → Configurar institución
o editando este archivo antes de compilar el instalador.
"""

import os
import sys

def _data_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "data")
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

_CONFIG_DIR = _data_dir()
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "institution_config.json")

DEFAULT_INSTITUTION = {
    "name": "Mi Institución",
    "address": "",
    "phone": "",
    "email": "",
    "web": "",
    "mp_number": "",
    "doctor_name": "",
    "logo_path": "",
    "watermark_path": "",
    "default_logo": "resources/default_logo.png",
    "footer_text": "Documento generado por HardForms © 2026",
    "theme": "light",
}


def _load_config():
    import json
    if os.path.isfile(_CONFIG_FILE):
        for enc in ("utf-8", "cp1252"):
            try:
                with open(_CONFIG_FILE, encoding=enc) as f:
                    return json.load(f)
            except Exception:
                continue
    return dict(DEFAULT_INSTITUTION)


def _save_config(cfg):
    import json
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _resource_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(__file__))


def get_institution():
    cfg = _load_config()
    base = _resource_dir()
    for key in ("logo_path", "watermark_path", "default_logo"):
        val = cfg.get(key, "")
        if val and not os.path.isabs(val):
            cfg[key] = os.path.join(base, val)
    return cfg


def is_default_config():
    cfg = _load_config()
    keys = list(DEFAULT_INSTITUTION.keys())
    return all(cfg.get(k) == DEFAULT_INSTITUTION[k] for k in keys)


def save_institution(cfg):
    base = _resource_dir()
    for key in ("logo_path", "watermark_path", "default_logo"):
        val = cfg.get(key, "")
        if val and val.startswith(base):
            cfg[key] = os.path.relpath(val, base)
    _save_config(cfg)


INSTITUTION = get_institution()
