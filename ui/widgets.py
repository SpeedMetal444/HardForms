from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt


class DateMaskEdit(QLineEdit):
    """QLineEdit que auto-formatea como DD/MM/AAAA."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("DD/MM/AAAA")
        self.setMaxLength(10)
        self.textChanged.connect(self._format_date)

    def _format_date(self, text: str):
        pos = self.cursorPosition()
        digits = [c for c in text if c.isdigit()]
        formatted = ""
        for i, d in enumerate(digits):
            if i == 2 or i == 4:
                formatted += "/"
            formatted += d
            if len(formatted) >= 10:
                break

        if formatted != text:
            self.blockSignals(True)
            old_pos = self.cursorPosition()
            self.setText(formatted)
            # Ajustar cursor
            new_pos = old_pos
            if len(formatted) > len(text):
                new_pos = old_pos + 1
            elif len(formatted) < len(text):
                new_pos = old_pos - 1
            self.setCursorPosition(min(new_pos, len(formatted)))
            self.blockSignals(False)
