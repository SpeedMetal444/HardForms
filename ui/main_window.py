import os
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QLabel, QToolBar,
    QStatusBar, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap
from database.db import get_all_patients, search_patients, delete_patient, get_patient, get_diagnoses_for_patient
from ui.patient_dialog import PatientDialog
from reports.pdf_generator import generate_patient_report
from config.institution import INSTITUTION


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"HardForms - {INSTITUTION['name']}")
        self.setMinimumSize(1100, 650)
        self._setup_ui()
        self._load_patients()

    def _setup_ui(self):
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        btn_new = QAction("Nuevo Paciente", self)
        btn_new.triggered.connect(self._on_new_patient)
        toolbar.addAction(btn_new)

        btn_edit = QAction("Editar", self)
        btn_edit.triggered.connect(self._on_edit_patient)
        toolbar.addAction(btn_edit)

        btn_delete = QAction("Eliminar", self)
        btn_delete.triggered.connect(self._on_delete_patient)
        toolbar.addAction(btn_delete)

        toolbar.addSeparator()

        btn_report = QAction("Generar Informe PDF", self)
        btn_report.triggered.connect(self._on_generate_pdf)
        toolbar.addAction(btn_report)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, apellido o DNI...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Patient table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Apellido", "Nombre", "DNI", "Teléfono", "Nro. Historia", "Última modificación"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(0, True)
        self.table.doubleClicked.connect(self._on_edit_patient)
        layout.addWidget(self.table)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _load_patients(self, query: str = ""):
        if query:
            patients = search_patients(query)
        else:
            patients = get_all_patients()

        self.table.setRowCount(len(patients))
        for i, p in enumerate(patients):
            self.table.setItem(i, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(i, 1, QTableWidgetItem(p.last_name))
            self.table.setItem(i, 2, QTableWidgetItem(p.first_name))
            self.table.setItem(i, 3, QTableWidgetItem(p.dni))
            self.table.setItem(i, 4, QTableWidgetItem(p.phone))
            self.table.setItem(i, 5, QTableWidgetItem(p.medical_record_number))
            self.table.setItem(i, 6, QTableWidgetItem(p.updated_at))

        self.table.resizeColumnsToContents()
        self.status_bar.showMessage(f"{len(patients)} paciente(s)")

    def _on_search(self, text: str):
        self._load_patients(text.strip())

    def _get_selected_patient_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccioná un paciente de la lista.")
            return None
        return int(self.table.item(row, 0).text())

    def _on_new_patient(self):
        dialog = PatientDialog(self)
        if dialog.exec():
            self._load_patients(self.search_input.text().strip())

    def _on_edit_patient(self):
        patient_id = self._get_selected_patient_id()
        if patient_id is None:
            return
        dialog = PatientDialog(self, patient_id)
        if dialog.exec():
            self._load_patients(self.search_input.text().strip())

    def _on_delete_patient(self):
        patient_id = self._get_selected_patient_id()
        if patient_id is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Eliminar este paciente? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_patient(patient_id)
            self._load_patients(self.search_input.text().strip())

    def _on_generate_pdf(self):
        patient_id = self._get_selected_patient_id()
        if patient_id is None:
            return

        patient = get_patient(patient_id)
        if patient is None:
            return

        diagnoses = get_diagnoses_for_patient(patient_id)
        diag_code = diagnoses[0].icd10_code if diagnoses else "sin-dx"
        safe_name = re.sub(r'[\\/*?:"<>|]', "", f"{patient.last_name}_{patient.first_name}")
        suggested = f"{safe_name}_{diag_code}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe PDF", suggested, "PDF (*.pdf)"
        )
        if not file_path:
            return
        try:
            generate_patient_report(patient_id, file_path)
            QMessageBox.information(self, "PDF generado", f"Informe guardado en:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF:\n{e}")
