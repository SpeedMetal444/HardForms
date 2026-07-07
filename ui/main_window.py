import os
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QLabel, QToolBar,
    QStatusBar, QAbstractItemView, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap
from database.db import get_all_patients, search_patients, delete_patient, get_patient, get_diagnoses_for_patient
from ui.patient_dialog import PatientDialog
from ui.patient_view import PatientView
from reports.pdf_generator import generate_patient_report
from config.institution import INSTITUTION
from importer import run_import
from ui.widgets import DateItem


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

        btn_import = QAction("Importar desde Access", self)
        btn_import.triggered.connect(self._on_import)
        toolbar.addAction(btn_import)

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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Apellido", "Nombre", "DNI", "Afiliado", "Fecha Estudio"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(0, True)
        self.table.doubleClicked.connect(self._on_view_patient)
        layout.addWidget(self.table)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _load_patients(self, query: str = ""):
        self.table.setSortingEnabled(False)

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
            self.table.setItem(i, 4, QTableWidgetItem(p.insurance))
            self.table.setItem(i, 5, DateItem(p.last_study_date))

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)
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

    def _on_view_patient(self):
        patient_id = self._get_selected_patient_id()
        if patient_id is None:
            return
        view = PatientView(self, patient_id)
        if view.exec():
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

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar base de datos .mdb", "",
            "Access Database (*.mdb);;Todos (*.*)"
        )
        if not file_path:
            return

        reply = QMessageBox.question(
            self, "Importar desde Access",
            "¿Importar pacientes desde archivo de base de datos .mdb?\n"
            "Los datos actuales se reemplazarán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        progress = QProgressDialog("Iniciando importación...", None, 0, 0, self)
        progress.setWindowTitle("Importando")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()

        def _progress(msg):
            progress.setLabelText(msg)
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()

        try:
            n_est, n_eco = run_import(mdb_path=file_path, progress=_progress)
            progress.close()
            QMessageBox.information(
                self, "Importación completada",
                f"Se importaron:\n"
                f"  - {n_est} pacientes de Estudios\n"
                f"  - {n_eco} pacientes de Ecografías\n"
                f"Total: {n_est + n_eco} pacientes."
            )
            self._load_patients(self.search_input.text().strip())
        except FileNotFoundError as e:
            progress.close()
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self, "Error de importación",
                f"Ocurrió un error durante la importación:\n{e}"
            )

    def _on_generate_pdf(self):
        patient_id = self._get_selected_patient_id()
        if patient_id is None:
            return

        patient = get_patient(patient_id)
        if patient is None:
            return

        diagnoses = get_diagnoses_for_patient(patient_id)
        diag_name = diagnoses[0].description if diagnoses else "sin-diagnostico"
        safe_name = re.sub(r'[\\/*?:"<>|]', "", f"{patient.last_name}_{patient.first_name}")
        safe_diag = re.sub(r'[\\/*?:"<>|]', "", diag_name)[:40]
        suggested = f"{safe_name}_{safe_diag}.pdf"

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
