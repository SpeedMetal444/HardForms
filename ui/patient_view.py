import os
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QScrollArea,
    QTableWidget, QTableWidgetItem, QGroupBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from database.db import get_patient, get_diagnoses_for_patient
from config.institution import INSTITUTION


class PatientView(QDialog):
    def __init__(self, parent=None, patient_id: int | None = None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle(f"Ficha del Paciente - {INSTITUTION['name']}")
        self.setMinimumSize(900, 750)
        self.resize(950, 800)
        self._setup_ui()
        if patient_id:
            self._load_patient(patient_id)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header buttons
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.clicked.connect(self._on_edit)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addStretch()
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        layout.addWidget(scroll)
        scroll.setWidget(scroll_content)

        # Patient info
        info_group = QGroupBox("Datos del Paciente")
        info_form = QFormLayout(info_group)

        self.lbl_name = QLabel()
        self.lbl_name.setWordWrap(True)
        info_form.addRow("Nombre:", self.lbl_name)

        self.lbl_last_name = QLabel()
        self.lbl_last_name.setWordWrap(True)
        info_form.addRow("Apellido:", self.lbl_last_name)

        self.lbl_dni = QLabel()
        info_form.addRow("DNI:", self.lbl_dni)

        self.lbl_birth_date = QLabel()
        info_form.addRow("Fecha de nacimiento:", self.lbl_birth_date)

        self.lbl_phone = QLabel()
        info_form.addRow("Teléfono:", self.lbl_phone)

        self.lbl_email = QLabel()
        info_form.addRow("Email:", self.lbl_email)

        self.lbl_address = QLabel()
        self.lbl_address.setWordWrap(True)
        info_form.addRow("Domicilio:", self.lbl_address)

        self.lbl_mrn = QLabel()
        info_form.addRow("Nro. Historia:", self.lbl_mrn)

        scroll_layout.addWidget(info_group)

        # Diagnoses
        diag_group = QGroupBox("Diagnósticos")
        diag_layout = QVBoxLayout(diag_group)
        self.diag_table = QTableWidget()
        self.diag_table.setColumnCount(2)
        self.diag_table.setHorizontalHeaderLabels(["Diagnóstico", "Fecha"])
        self.diag_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.diag_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.diag_table.horizontalHeader().setStretchLastSection(True)
        self.diag_table.setMinimumHeight(100)
        diag_layout.addWidget(self.diag_table)
        scroll_layout.addWidget(diag_group)

        # Description
        desc_group = QGroupBox("Descripción / Informe Médico")
        desc_layout = QVBoxLayout(desc_group)
        self.lbl_description = QLabel()
        self.lbl_description.setWordWrap(True)
        self.lbl_description.setTextFormat(Qt.TextFormat.PlainText)
        desc_layout.addWidget(self.lbl_description)
        scroll_layout.addWidget(desc_group)

        # Images
        img_group = QGroupBox("Imágenes adjuntas")
        img_layout = QVBoxLayout(img_group)
        self.img_preview = QLabel("(sin imágenes)")
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setMinimumHeight(200)
        self.img_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        img_layout.addWidget(self.img_preview)
        scroll_layout.addWidget(img_group)

    def _load_patient(self, patient_id: int):
        p = get_patient(patient_id)
        if p is None:
            return

        self.lbl_name.setText(p.first_name or "-")
        self.lbl_last_name.setText(p.last_name or "-")
        self.lbl_dni.setText(p.dni or "-")
        self.lbl_birth_date.setText(p.birth_date or "-")
        self.lbl_phone.setText(p.phone or "-")
        self.lbl_email.setText(p.email or "-")
        self.lbl_address.setText(p.address or "-")
        self.lbl_mrn.setText(p.medical_record_number or "-")
        self.lbl_description.setText(p.description or "(sin informe)")

        # Diagnoses
        self.diagnoses = get_diagnoses_for_patient(patient_id)
        self.diag_table.setRowCount(len(self.diagnoses))
        for i, d in enumerate(self.diagnoses):
            self.diag_table.setItem(i, 0, QTableWidgetItem(d.description))
            self.diag_table.setItem(i, 1, QTableWidgetItem(d.date))
        self.diag_table.resizeColumnsToContents()

        # Images
        if p.attachments:
            first = p.attachments[0]
            pixmap = QPixmap(first.path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    600, 300, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.img_preview.setPixmap(scaled)
                if first.description:
                    self.img_preview.setToolTip(first.description)
        else:
            self.img_preview.setText("(sin imágenes)")

    def _on_edit(self):
        from ui.patient_dialog import PatientDialog
        dialog = PatientDialog(self, self.patient_id)
        if dialog.exec():
            self._load_patient(self.patient_id)
