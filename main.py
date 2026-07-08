import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from database.db import init_db
from ui.main_window import MainWindow


def _data_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "data")
    return os.path.join(os.path.dirname(__file__), "data")


def _resource_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(__file__)


def _load_qss(theme):
    qss_file = os.path.join(_resource_dir(), "resources", f"{theme}.qss")
    if os.path.isfile(qss_file):
        with open(qss_file, encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    os.makedirs(_data_dir(), exist_ok=True)
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("HardForms")
    icon_path = os.path.join(_resource_dir(), "resources", "default_logo.png")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    from config.institution import get_institution
    theme = get_institution().get("theme", "light")
    qss = _load_qss(theme)
    if qss:
        app.setStyleSheet(qss)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
