import os
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QScrollArea,
    QTableWidget, QTableWidgetItem, QGroupBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices
from database.db import get_patient, get_diagnoses_for_patient
from config.institution import get_institution
from reports.pdf_generator import generate_patient_report


class PatientView(QDialog):
    def __init__(self, parent=None, patient_id: int | None = None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle(f"Ficha del Paciente - {get_institution()['name']}")
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
        self.btn_print = QPushButton("Abrir como PDF")
        self.btn_print.clicked.connect(self._on_print)
        btn_layout.addWidget(self.btn_print)
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

        self.lbl_insurance = QLabel()
        info_form.addRow("Afiliado:", self.lbl_insurance)

        self.lbl_insurance_number = QLabel()
        info_form.addRow("Afiliado Nº:", self.lbl_insurance_number)

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

        self.lbl_doctor = QLabel()
        info_form.addRow("Médico operador:", self.lbl_doctor)

        self.lbl_referring_doctor = QLabel()
        info_form.addRow("Médico derivante:", self.lbl_referring_doctor)

        self.lbl_study_type = QLabel()
        info_form.addRow("Tipo estudio:", self.lbl_study_type)

        self.lbl_center = QLabel()
        info_form.addRow("Centro:", self.lbl_center)

        scroll_layout.addWidget(info_group)

        # Anestesia / Preparación
        anes_group = QGroupBox("Anestesia / Preparación")
        anes_form = QFormLayout(anes_group)

        self.lbl_anesthesia_type = QLabel()
        anes_form.addRow("Tipo:", self.lbl_anesthesia_type)

        self.lbl_drug = QLabel()
        anes_form.addRow("Droga:", self.lbl_drug)

        self.lbl_postop = QLabel()
        anes_form.addRow("Postoperatorio:", self.lbl_postop)

        self.lbl_anesthesiologist = QLabel()
        anes_form.addRow("Anestesiólogo:", self.lbl_anesthesiologist)

        self.lbl_boston = QLabel()
        anes_form.addRow("Escala de Boston:", self.lbl_boston)

        scroll_layout.addWidget(anes_group)

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
        self.img_scroll = QScrollArea()
        self.img_scroll.setWidgetResizable(True)
        self.img_scroll.setMinimumHeight(250)
        self.img_scroll_content = QWidget()
        self.img_grid = QVBoxLayout(self.img_scroll_content)
        self.img_scroll.setWidget(self.img_scroll_content)
        img_layout.addWidget(self.img_scroll)
        scroll_layout.addWidget(img_group)

    def _load_patient(self, patient_id: int):
        p = get_patient(patient_id)
        if p is None:
            return

        self.lbl_name.setText(p.first_name or "-")
        self.lbl_last_name.setText(p.last_name or "-")
        self.lbl_dni.setText(p.dni or "-")
        self.lbl_insurance.setText(p.insurance or "-")
        self.lbl_insurance_number.setText(p.insurance_number or "-")
        self.lbl_birth_date.setText(p.birth_date or "-")
        self.lbl_phone.setText(p.phone or "-")
        self.lbl_email.setText(p.email or "-")
        self.lbl_address.setText(p.address or "-")
        self.lbl_mrn.setText(p.medical_record_number or "-")
        self.lbl_doctor.setText(p.doctor or "-")
        self.lbl_referring_doctor.setText(p.referring_doctor or "-")
        self.lbl_study_type.setText(p.study_type or "-")
        self.lbl_center.setText(p.center or "-")
        self.lbl_anesthesia_type.setText(p.anesthesia_type or "-")
        self.lbl_drug.setText(p.drug or "-")
        self.lbl_postop.setText(p.postop or "-")
        self.lbl_anesthesiologist.setText(p.anesthesiologist or "-")
        self.lbl_boston.setText(p.boston_scale or "-")
        self.lbl_description.setText(p.description or "(sin informe)")

        # Diagnoses
        self.diagnoses = get_diagnoses_for_patient(patient_id)
        self.diag_table.setRowCount(len(self.diagnoses))
        for i, d in enumerate(self.diagnoses):
            self.diag_table.setItem(i, 0, QTableWidgetItem(d.description))
            self.diag_table.setItem(i, 1, QTableWidgetItem(d.date))
        self.diag_table.resizeColumnsToContents()

        # Images
        for i in reversed(range(self.img_grid.count())):
            widget = self.img_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if p.attachments:
            row_layout = None
            for idx, att in enumerate(p.attachments):
                if idx % 2 == 0:
                    row_layout = QHBoxLayout()
                    self.img_grid.addLayout(row_layout)
                cell = QVBoxLayout()
                pixmap = QPixmap(att.path)
                label = QLabel()
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        280, 200, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    label.setPixmap(scaled)
                else:
                    label.setText(f"(no encontrada: {os.path.basename(att.path)})")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
                cell.addWidget(label)
                if att.description:
                    desc = QLabel(att.description)
                    desc.setWordWrap(True)
                    desc.setStyleSheet(
                        "font-size: 12pt; font-weight: bold; color: #1A5276; "
                        "background-color: #D4E6F1; border: 2px solid #2980B9; "
                        "border-radius: 6px; padding: 10px; margin-top: 6px;"
                    )
                    cell.addWidget(desc)
                cell.addStretch()
                row_layout.addLayout(cell)
        else:
            empty = QLabel("(sin imágenes)")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(100)
            empty.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; color: #888;")
            self.img_grid.addWidget(empty)

    def _on_edit(self):
        from ui.patient_dialog import PatientDialog
        dialog = PatientDialog(self, self.patient_id)
        if dialog.exec():
            self._load_patient(self.patient_id)

    def _on_print(self):
        if not self.patient_id:
            return
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        try:
            generate_patient_report(self.patient_id, tmp.name)
            QDesktopServices.openUrl(QUrl.fromLocalFile(tmp.name))
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"No se pudo generar el informe:\n{e}")
