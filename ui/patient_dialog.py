import os
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QScrollArea,
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox, QGroupBox, QGridLayout, QAbstractItemView,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from models.patient import Patient
from database.db import insert_patient, update_patient, get_patient


class PatientDialog(QDialog):
    def __init__(self, parent=None, patient_id: int | None = None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.image_paths: list[str] = []
        self.setWindowTitle("Editar Paciente" if patient_id else "Nuevo Paciente")
        self.setMinimumSize(800, 650)
        self._setup_ui()

        if patient_id:
            self._load_patient(patient_id)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Form fields
        form = QFormLayout()

        self.input_first_name = QLineEdit()
        self.input_first_name.setPlaceholderText("Nombre")
        form.addRow("Nombre:", self.input_first_name)

        self.input_last_name = QLineEdit()
        self.input_last_name.setPlaceholderText("Apellido")
        form.addRow("Apellido:", self.input_last_name)

        self.input_dni = QLineEdit()
        self.input_dni.setPlaceholderText("DNI")
        form.addRow("DNI:", self.input_dni)

        self.input_birth_date = QLineEdit()
        self.input_birth_date.setPlaceholderText("DD/MM/AAAA")
        form.addRow("Fecha de nacimiento:", self.input_birth_date)

        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("Teléfono")
        form.addRow("Teléfono:", self.input_phone)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email")
        form.addRow("Email:", self.input_email)

        self.input_address = QLineEdit()
        self.input_address.setPlaceholderText("Domicilio")
        form.addRow("Domicilio:", self.input_address)

        self.input_mrn = QLineEdit()
        self.input_mrn.setPlaceholderText("Nro. Historia Clínica")
        form.addRow("Nro. Historia:", self.input_mrn)

        layout.addLayout(form)

        # Description
        desc_group = QGroupBox("Descripción / Informe Médico")
        desc_layout = QVBoxLayout(desc_group)
        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText("Escribí aquí el informe médico...")
        self.input_description.setMinimumHeight(120)
        desc_layout.addWidget(self.input_description)
        layout.addWidget(desc_group)

        # Images
        img_group = QGroupBox("Imágenes adjuntas")
        img_layout = QVBoxLayout(img_group)

        btn_img_layout = QHBoxLayout()
        btn_add_img = QPushButton("Agregar imagen")
        btn_add_img.clicked.connect(self._on_add_image)
        btn_remove_img = QPushButton("Quitar seleccionada")
        btn_remove_img.clicked.connect(self._on_remove_image)
        btn_img_layout.addWidget(btn_add_img)
        btn_img_layout.addWidget(btn_remove_img)
        btn_img_layout.addStretch()
        img_layout.addLayout(btn_img_layout)

        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.image_list.currentRowChanged.connect(self._on_preview_image)
        img_layout.addWidget(self.image_list)

        self.image_preview = QLabel("Vista previa")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(150)
        self.image_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        img_layout.addWidget(self.image_preview)

        layout.addWidget(img_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_patient(self, patient_id: int):
        p = get_patient(patient_id)
        if p is None:
            return
        self.input_first_name.setText(p.first_name)
        self.input_last_name.setText(p.last_name)
        self.input_dni.setText(p.dni)
        self.input_birth_date.setText(p.birth_date)
        self.input_phone.setText(p.phone)
        self.input_email.setText(p.email)
        self.input_address.setText(p.address)
        self.input_mrn.setText(p.medical_record_number)
        self.input_description.setPlainText(p.description)
        self.image_paths = list(p.image_paths)
        self._refresh_image_list()

    def _on_add_image(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes",
            "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        for f in files:
            if f not in self.image_paths:
                self.image_paths.append(f)
        self._refresh_image_list()

    def _on_remove_image(self):
        row = self.image_list.currentRow()
        if row >= 0 and row < len(self.image_paths):
            self.image_paths.pop(row)
            self._refresh_image_list()

    def _refresh_image_list(self):
        self.image_list.blockSignals(True)
        self.image_list.clear()
        for path in self.image_paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            self.image_list.addItem(item)
        self.image_list.blockSignals(False)
        if self.image_paths:
            self.image_list.setCurrentRow(0)
        else:
            self.image_preview.clear()
            self.image_preview.setText("Vista previa")

    def _on_preview_image(self, row: int):
        if row < 0 or row >= len(self.image_paths):
            self.image_preview.clear()
            self.image_preview.setText("Vista previa")
            return
        pixmap = QPixmap(self.image_paths[row])
        if pixmap.isNull():
            self.image_preview.setText("(no se puede previsualizar)")
            return
        scaled = pixmap.scaled(
            400, 200, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_preview.setPixmap(scaled)

    def _on_accept(self):
        first_name = self.input_first_name.text().strip()
        last_name = self.input_last_name.text().strip()
        if not first_name or not last_name:
            QMessageBox.warning(self, "Campos requeridos", "Nombre y Apellido son obligatorios.")
            return

        p = Patient(
            id=self.patient_id,
            first_name=first_name,
            last_name=last_name,
            dni=self.input_dni.text().strip(),
            birth_date=self.input_birth_date.text().strip(),
            phone=self.input_phone.text().strip(),
            email=self.input_email.text().strip(),
            address=self.input_address.text().strip(),
            medical_record_number=self.input_mrn.text().strip(),
            description=self.input_description.toPlainText().strip(),
            image_paths=self.image_paths,
        )

        if self.patient_id:
            update_patient(p)
        else:
            insert_patient(p)

        self.accept()
