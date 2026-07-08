import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from database.db import init_db
from ui.main_window import MainWindow


def main():
    # Ensure data directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("HardForms")
    icon_path = os.path.join(os.path.dirname(__file__), "resources", "default_logo.png")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
