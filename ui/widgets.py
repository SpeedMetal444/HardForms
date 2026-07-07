from PyQt6.QtWidgets import QLineEdit, QTableWidgetItem
from PyQt6.QtCore import Qt


def _to_sortable_date(d: str) -> str:
    """Convierte DD/MM/AAAA a AAAA/MM/DD para ordenar."""
    if not d or len(d) != 10:
        return d
    return f"{d[6:]}/{d[3:5]}/{d[:2]}"


class DateItem(QTableWidgetItem):
    """QTableWidgetItem que ordena fechas DD/MM/AAAA cronológicamente."""
    def __init__(self, date_str: str):
        super().__init__(date_str)
        self._sort_key = _to_sortable_date(date_str)
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        if isinstance(other, DateItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)


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
            new_pos = old_pos
            if len(formatted) > len(text):
                new_pos = old_pos + 1
            elif len(formatted) < len(text):
                new_pos = old_pos - 1
            self.setCursorPosition(min(new_pos, len(formatted)))
            self.blockSignals(False)
