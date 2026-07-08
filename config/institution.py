"""
CONFIGURACIÓN DE LA INSTITUCIÓN
================================
Personalizá estos valores desde el menú Herramientas → Configurar institución
o editando este archivo antes de compilar el instalador.
"""

import os

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
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
    "default_logo": "resources/default_logo.png",
    "footer_text": "Documento generado por HardForms © 2026",
}


def _load_config():
    import json
    if os.path.isfile(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(DEFAULT_INSTITUTION)


def _save_config(cfg):
    import json
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_institution():
    cfg = _load_config()
    # resolver rutas relativas
    base = os.path.dirname(os.path.dirname(__file__))
    for key in ("logo_path", "default_logo"):
        val = cfg.get(key, "")
        if val and not os.path.isabs(val):
            cfg[key] = os.path.join(base, val)
    return cfg


def save_institution(cfg):
    # guardar rutas como relativas
    base = os.path.dirname(os.path.dirname(__file__))
    for key in ("logo_path", "default_logo"):
        val = cfg.get(key, "")
        if val and val.startswith(base):
            cfg[key] = os.path.relpath(val, base)
    _save_config(cfg)


INSTITUTION = get_institution()
