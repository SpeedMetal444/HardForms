import os
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QFileDialog, QMessageBox, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from config.institution import get_institution, save_institution


class InstitutionSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Institución")
        self.setMinimumWidth(500)
        self._cfg = get_institution()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.input_name = QLineEdit(self._cfg.get("name", ""))
        self.input_name.setPlaceholderText("Ej: Centro Médico Buenos Aires")
        form.addRow("Nombre de la institución:", self.input_name)

        self.input_address = QLineEdit(self._cfg.get("address", ""))
        self.input_address.setPlaceholderText("Ej: Av. Corrientes 1234, CABA")
        form.addRow("Dirección:", self.input_address)

        self.input_phone = QLineEdit(self._cfg.get("phone", ""))
        self.input_phone.setPlaceholderText("Ej: +54 11 1234-5678")
        form.addRow("Teléfono:", self.input_phone)

        self.input_email = QLineEdit(self._cfg.get("email", ""))
        self.input_email.setPlaceholderText("Ej: contacto@micentro.com")
        form.addRow("Email:", self.input_email)

        self.input_web = QLineEdit(self._cfg.get("web", ""))
        self.input_web.setPlaceholderText("Ej: www.micentro.com")
        form.addRow("Sitio web:", self.input_web)

        self.input_mp = QLineEdit(self._cfg.get("mp_number", ""))
        self.input_mp.setPlaceholderText("Ej: MP 12345")
        form.addRow("Nro. Matrícula (MP):", self.input_mp)

        self.input_doctor = QLineEdit(self._cfg.get("doctor_name", ""))
        self.input_doctor.setPlaceholderText("Ej: Dr. Juan Pérez")
        form.addRow("Médico / Director:", self.input_doctor)

        # Logo
        logo_layout = QHBoxLayout()
        self._logo_path = self._cfg.get("logo_path", "")
        self.lbl_logo_path = QLabel(self._logo_path if self._logo_path else "(ninguno)")
        self.lbl_logo_path.setStyleSheet("color: #7F8C8D;")
        btn_logo = QPushButton("Seleccionar logo...")
        btn_logo.clicked.connect(self._on_select_logo)
        btn_clear_logo = QPushButton("Quitar")
        btn_clear_logo.clicked.connect(self._on_clear_logo)
        logo_layout.addWidget(self.lbl_logo_path, 1)
        logo_layout.addWidget(btn_logo)
        logo_layout.addWidget(btn_clear_logo)
        form.addRow("Logo institucional:", logo_layout)

        # Marca de agua
        wm_layout = QHBoxLayout()
        self._watermark_path = self._cfg.get("watermark_path", "")
        self.lbl_watermark_path = QLabel(self._watermark_path if self._watermark_path else "(ninguno)")
        self.lbl_watermark_path.setStyleSheet("color: #7F8C8D;")
        btn_wm = QPushButton("Seleccionar imagen...")
        btn_wm.clicked.connect(self._on_select_watermark)
        btn_clear_wm = QPushButton("Quitar")
        btn_clear_wm.clicked.connect(self._on_clear_watermark)
        wm_layout.addWidget(self.lbl_watermark_path, 1)
        wm_layout.addWidget(btn_wm)
        wm_layout.addWidget(btn_clear_wm)
        form.addRow("Imagen marca de agua:", wm_layout)

        layout.addLayout(form)
        layout.addSpacing(12)

        # Preview del logo
        self.preview = QLabel()
        self.preview.setFixedSize(200, 100)
        self.preview.setStyleSheet("border: 1px solid #BDC3C7; background: #F8F9FA;")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_preview()
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(12)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_select_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._logo_path = path
            self.lbl_logo_path.setText(path)
            self._update_preview()

    def _on_clear_logo(self):
        self._logo_path = ""
        self.lbl_logo_path.setText("(ninguno)")
        self.preview.clear()
        self.preview.setText("Sin logo")

    def _on_select_watermark(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen para marca de agua", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._watermark_path = path
            self.lbl_watermark_path.setText(path)

    def _on_clear_watermark(self):
        self._watermark_path = ""
        self.lbl_watermark_path.setText("(ninguno)")

    def _update_preview(self):
        if self._logo_path and os.path.isfile(self._logo_path):
            pix = QPixmap(self._logo_path)
            if not pix.isNull():
                pix = pix.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
                self.preview.setPixmap(pix)
                return
        self.preview.setText("Sin logo")

    def _on_accept(self):
        cfg = dict(self._cfg)
        cfg.update({
            "name": self.input_name.text().strip(),
            "address": self.input_address.text().strip(),
            "phone": self.input_phone.text().strip(),
            "email": self.input_email.text().strip(),
            "web": self.input_web.text().strip(),
            "mp_number": self.input_mp.text().strip(),
            "doctor_name": self.input_doctor.text().strip(),
            "logo_path": self._logo_path,
            "watermark_path": self._watermark_path,
            "footer_text": "Documento generado por HardForms © 2026",
        })
        save_institution(cfg)
        QMessageBox.information(self, "Guardado",
                                "Configuración guardada correctamente.\n"
                                "Los cambios se aplicarán al reiniciar el programa.")
        self.accept()
