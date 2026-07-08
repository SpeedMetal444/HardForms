import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QScrollArea,
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox, QGroupBox, QAbstractItemView,
    QTableWidget, QTableWidgetItem, QInputDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QComboBox, QButtonGroup, QRadioButton
from ui.widgets import DateMaskEdit
from models.patient import Patient, ImageAttachment
from models.diagnosis import Diagnosis
from database.db import (
    insert_patient, update_patient, get_patient,
    get_diagnoses_for_patient, insert_diagnosis,
    delete_diagnoses_for_patient, get_next_medical_record_number,
    get_lookup_list, add_lookup_value,
)


class PatientDialog(QDialog):
    def __init__(self, parent=None, patient_id: int | None = None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.attachments: list[ImageAttachment] = []
        self.diagnoses: list[Diagnosis] = []
        self.setWindowTitle("Editar Paciente" if patient_id else "Nuevo Paciente")
        self.setMinimumSize(900, 750)
        self.resize(950, 800)
        self._setup_ui()

        if patient_id:
            self._load_patient(patient_id)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        layout.addWidget(scroll)
        scroll.setWidget(scroll_content)

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

        self.input_insurance = QLineEdit()
        self.input_insurance.setPlaceholderText("Ej: OSDE, OSPEP")
        form.addRow("Afiliado:", self.input_insurance)

        self.input_insurance_number = QLineEdit()
        self.input_insurance_number.setPlaceholderText("Nº de afiliado")
        form.addRow("Afiliado Nº:", self.input_insurance_number)

        self.input_birth_date = DateMaskEdit()
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
        self.input_mrn.setReadOnly(True)
        self.input_mrn.setStyleSheet("background-color: #f0f0f0;")
        if not self.patient_id:
            self.input_mrn.setText(get_next_medical_record_number())
        form.addRow("Nro. Historia:", self.input_mrn)

        scroll_layout.addLayout(form)

        # Médico operador
        self.input_doctor = self._make_combo("doctor", "Médico operador")
        form.addRow("Médico operador:", self.input_doctor)

        scroll_layout.addLayout(form)

        # Médico derivante / Estudio
        self.input_referring_doctor = self._make_combo("referring_doctor", "Médico derivante")
        form.addRow("Médico derivante:", self.input_referring_doctor)

        self.input_study_type = QLineEdit()
        self.input_study_type.setPlaceholderText("Tipo de estudio")
        form.addRow("Tipo estudio:", self.input_study_type)

        self.input_center = QLineEdit()
        self.input_center.setPlaceholderText("Centro")
        form.addRow("Centro:", self.input_center)

        # Anestesia / Preparación
        anes_group = QGroupBox("Anestesia / Preparación")
        anes_layout = QFormLayout(anes_group)

        self.tipo_group = QButtonGroup(self)
        tipo_layout = QHBoxLayout()
        self.rb_tipo_local = QRadioButton("Local")
        self.rb_tipo_general = QRadioButton("General")
        self.tipo_group.addButton(self.rb_tipo_local)
        self.tipo_group.addButton(self.rb_tipo_general)
        tipo_layout.addWidget(self.rb_tipo_local)
        tipo_layout.addWidget(self.rb_tipo_general)
        tipo_layout.addStretch()
        anes_layout.addRow("Tipo:", tipo_layout)

        self.input_drug = QLineEdit()
        self.input_drug.setPlaceholderText("Droga utilizada")
        self.input_drug.textChanged.connect(self._on_drug_changed)
        anes_layout.addRow("Droga:", self.input_drug)

        self.input_postop = QLineEdit()
        self.input_postop.setPlaceholderText("Postoperatorio")
        anes_layout.addRow("Postoperatorio:", self.input_postop)

        self.input_anesthesiologist = self._make_combo("anesthesiologist", "Anestesiólogo")
        anes_layout.addRow("Anestesiólogo:", self.input_anesthesiologist)

        self.input_boston = QComboBox()
        self.input_boston.setEditable(True)
        self.input_boston.addItems(["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
        anes_layout.addRow("Escala de Boston (0-9):", self.input_boston)

        scroll_layout.addWidget(anes_group)

        # Diagnoses section
        diag_group = QGroupBox("Diagnósticos")
        diag_layout = QVBoxLayout(diag_group)

        btn_diag_layout = QHBoxLayout()
        btn_add_diag = QPushButton("Agregar diagnóstico")
        btn_add_diag.clicked.connect(self._on_add_diagnosis)
        btn_edit_diag = QPushButton("Editar")
        btn_edit_diag.clicked.connect(self._on_edit_diagnosis)
        btn_del_diag = QPushButton("Quitar")
        btn_del_diag.clicked.connect(self._on_remove_diagnosis)
        btn_diag_layout.addWidget(btn_add_diag)
        btn_diag_layout.addWidget(btn_edit_diag)
        btn_diag_layout.addWidget(btn_del_diag)
        btn_diag_layout.addStretch()
        diag_layout.addLayout(btn_diag_layout)

        self.diag_table = QTableWidget()
        self.diag_table.setColumnCount(2)
        self.diag_table.setHorizontalHeaderLabels(["Diagnóstico", "Fecha"])
        self.diag_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.diag_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.diag_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.diag_table.horizontalHeader().setStretchLastSection(True)
        self.diag_table.setMinimumHeight(100)
        diag_layout.addWidget(self.diag_table)

        scroll_layout.addWidget(diag_group)

        # Description
        desc_group = QGroupBox("Descripción / Informe Médico")
        desc_layout = QVBoxLayout(desc_group)
        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText("Escribí aquí el informe médico...")
        self.input_description.setMinimumHeight(120)
        desc_layout.addWidget(self.input_description)
        scroll_layout.addWidget(desc_group)

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

        img_content = QHBoxLayout()

        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_list.setIconSize(QSize(100, 80))
        self.image_list.setGridSize(QSize(120, 110))
        self.image_list.setWordWrap(True)
        self.image_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.image_list.currentRowChanged.connect(self._on_select_image)
        self.image_list.setMinimumWidth(260)
        img_content.addWidget(self.image_list, 2)

        right_panel = QVBoxLayout()
        self.image_preview = QLabel("Vista previa")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(200)
        self.image_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        right_panel.addWidget(self.image_preview, 1)

        desc_img_layout = QHBoxLayout()
        desc_img_layout.addWidget(QLabel("Descripción:"))
        self.input_img_desc = QLineEdit()
        self.input_img_desc.setPlaceholderText("Breve descripción de esta imagen...")
        self.input_img_desc.textChanged.connect(self._on_desc_changed)
        desc_img_layout.addWidget(self.input_img_desc)
        right_panel.addLayout(desc_img_layout)

        img_content.addLayout(right_panel, 3)
        img_layout.addLayout(img_content)

        scroll_layout.addWidget(img_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        scroll_layout.addWidget(buttons)

    def _make_combo(self, list_type: str, placeholder: str) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setPlaceholderText(placeholder)
        combo.addItems(get_lookup_list(list_type))
        return combo

    def _save_combo_value(self, combo: QComboBox, list_type: str):
        val = combo.currentText().strip()
        if val:
            add_lookup_value(list_type, val)

    def _load_patient(self, patient_id: int):
        p = get_patient(patient_id)
        if p is None:
            return
        self.input_first_name.setText(p.first_name)
        self.input_last_name.setText(p.last_name)
        self.input_dni.setText(p.dni)
        self.input_insurance.setText(p.insurance)
        self.input_insurance_number.setText(p.insurance_number)
        self.input_birth_date.setText(p.birth_date)
        self.input_phone.setText(p.phone)
        self.input_email.setText(p.email)
        self.input_address.setText(p.address)
        self.input_mrn.setText(p.medical_record_number)
        self.input_doctor.setCurrentText(p.doctor)
        self.input_referring_doctor.setCurrentText(p.referring_doctor)
        self.input_study_type.setText(p.study_type)
        self.input_center.setText(p.center)
        if p.anesthesia_type == "General":
            self.rb_tipo_general.setChecked(True)
        elif p.anesthesia_type == "Local":
            self.rb_tipo_local.setChecked(True)
        self.input_drug.setText(p.drug)
        self._on_drug_changed(p.drug)
        self.input_postop.setText(p.postop)
        self.input_anesthesiologist.setCurrentText(p.anesthesiologist)
        self.input_boston.setCurrentText(p.boston_scale)
        self.input_description.setPlainText(p.description)
        self.attachments = [ImageAttachment(path=a.path, description=a.description) for a in p.attachments]
        self.diagnoses = get_diagnoses_for_patient(patient_id)
        self._refresh_image_list()
        self._refresh_diag_table()

    # --- Diagnoses ---

    def _on_add_diagnosis(self):
        diag = self._diagnosis_dialog()
        if diag:
            self.diagnoses.append(diag)
            self._refresh_diag_table()

    def _on_edit_diagnosis(self):
        row = self.diag_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccioná un diagnóstico.")
            return
        diag = self.diagnoses[row]
        updated = self._diagnosis_dialog(diag)
        if updated:
            self.diagnoses[row] = updated
            self._refresh_diag_table()

    def _on_remove_diagnosis(self):
        row = self.diag_table.currentRow()
        if row < 0:
            return
        self.diagnoses.pop(row)
        self._refresh_diag_table()

    def _diagnosis_dialog(self, existing: Diagnosis | None = None) -> Diagnosis | None:
        desc, ok = QInputDialog.getText(
            self, "Diagnóstico", "Descripción del diagnóstico:",
            text=existing.description if existing else ""
        )
        if not ok or not desc.strip():
            return None
        today = datetime.now().strftime("%d/%m/%Y")
        default_date = existing.date if existing else today
        date, ok = QInputDialog.getText(
            self, "Fecha", "Fecha (DD/MM/AAAA):",
            text=default_date
        )
        if not ok:
            return None
        return Diagnosis(
            id=existing.id if existing else None,
            patient_id=existing.patient_id if existing else (self.patient_id or 0),
            description=desc.strip(),
            date=date.strip() or today,
        )

    def _refresh_diag_table(self):
        self.diag_table.setRowCount(len(self.diagnoses))
        for i, d in enumerate(self.diagnoses):
            self.diag_table.setItem(i, 0, QTableWidgetItem(d.description))
            self.diag_table.setItem(i, 1, QTableWidgetItem(d.date))
        self.diag_table.resizeColumnsToContents()

    # --- Images ---

    def _on_add_image(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes",
            "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        for f in files:
            if not any(a.path == f for a in self.attachments):
                self.attachments.append(ImageAttachment(path=f, description=""))
        self._refresh_image_list()

    def _on_remove_image(self):
        row = self.image_list.currentRow()
        if row >= 0 and row < len(self.attachments):
            self.attachments.pop(row)
            self._refresh_image_list()

    def _refresh_image_list(self):
        self.image_list.blockSignals(True)
        self.image_list.clear()
        for att in self.attachments:
            label = os.path.basename(att.path)
            if att.description:
                label += f"\n{att.description}"
            item = QListWidgetItem(label)
            item.setToolTip(f"{att.path}\n{att.description}" if att.description else att.path)
            pixmap = QPixmap(att.path)
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap.scaled(100, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation)))
            self.image_list.addItem(item)
        self.image_list.blockSignals(False)
        if self.attachments:
            self.image_list.setCurrentRow(0)
        else:
            self.image_preview.clear()
            self.image_preview.setText("Vista previa")
            self.input_img_desc.setText("")

    def _on_select_image(self, row: int):
        self.input_img_desc.blockSignals(True)
        if row < 0 or row >= len(self.attachments):
            self.image_preview.clear()
            self.image_preview.setText("Vista previa")
            self.input_img_desc.setText("")
            self.input_img_desc.blockSignals(False)
            return

        att = self.attachments[row]
        self.input_img_desc.setText(att.description)

        pixmap = QPixmap(att.path)
        if pixmap.isNull():
            self.image_preview.setText("(no se puede previsualizar)")
        else:
            scaled = pixmap.scaled(
                400, 200, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(scaled)
        self.input_img_desc.blockSignals(False)

    def _on_desc_changed(self, text: str):
        row = self.image_list.currentRow()
        if row >= 0 and row < len(self.attachments):
            self.attachments[row].description = text
            label = os.path.basename(self.attachments[row].path)
            if text:
                label += f"\n{text}"
            self.image_list.currentItem().setText(label)

    def _on_drug_changed(self, text: str):
        enabled = bool(text.strip())
        self.rb_tipo_local.setEnabled(enabled)
        self.rb_tipo_general.setEnabled(enabled)

    def _on_accept(self):
        first_name = self.input_first_name.text().strip()
        last_name = self.input_last_name.text().strip()
        if not first_name or not last_name:
            QMessageBox.warning(self, "Campos requeridos", "Nombre y Apellido son obligatorios.")
            return

        self._save_combo_value(self.input_doctor, "doctor")
        self._save_combo_value(self.input_anesthesiologist, "anesthesiologist")

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
            insurance=self.input_insurance.text().strip(),
            insurance_number=self.input_insurance_number.text().strip(),
            doctor=self.input_doctor.currentText().strip(),
            referring_doctor=self.input_referring_doctor.currentText().strip(),
            study_type=self.input_study_type.text().strip(),
            center=self.input_center.text().strip(),
            anesthesia_type="General" if self.rb_tipo_general.isChecked() else "Local",
            drug=self.input_drug.text().strip(),
            postop=self.input_postop.text().strip(),
            anesthesiologist=self.input_anesthesiologist.currentText().strip(),
            boston_scale=self.input_boston.currentText().strip(),
            description=self.input_description.toPlainText().strip(),
            attachments=self.attachments,
        )

        if self.patient_id:
            update_patient(p)
            delete_diagnoses_for_patient(self.patient_id)
        else:
            self.patient_id = insert_patient(p)

        for d in self.diagnoses:
            d.patient_id = self.patient_id
            insert_diagnosis(d)

        self.accept()
