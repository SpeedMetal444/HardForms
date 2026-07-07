import os
import tempfile
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QLabel,
    QStatusBar, QAbstractItemView, QProgressDialog, QMenuBar,
)
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QAction, QIcon, QPixmap, QDesktopServices
from database.db import get_all_patients, search_patients, delete_patient, get_patient, get_diagnoses_for_patient, insert_patient, insert_diagnosis
from models.diagnosis import Diagnosis
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
        # Menu bar
        menubar = QMenuBar()
        self.setMenuBar(menubar)

        menu_archivo = menubar.addMenu("Archivo")
        act_new = QAction("Nuevo Paciente", self)
        act_new.triggered.connect(self._on_new_patient)
        menu_archivo.addAction(act_new)
        act_edit = QAction("Editar", self)
        act_edit.triggered.connect(self._on_edit_patient)
        menu_archivo.addAction(act_edit)
        act_delete = QAction("Eliminar", self)
        act_delete.triggered.connect(self._on_delete_patient)
        menu_archivo.addAction(act_delete)
        menu_archivo.addSeparator()

        menu_import = menu_archivo.addMenu("Importar")
        act_import_mdb_csv = QAction("CSV / MDB...", self)
        act_import_mdb_csv.triggered.connect(self._on_import)
        menu_import.addAction(act_import_mdb_csv)
        act_import_zip = QAction("Restaurar desde ZIP...", self)
        act_import_zip.triggered.connect(self._on_import_zip)
        menu_import.addAction(act_import_zip)

        menu_export = menu_archivo.addMenu("Exportar")
        act_export_csv = QAction("CSV...", self)
        act_export_csv.triggered.connect(self._on_export_csv)
        menu_export.addAction(act_export_csv)
        act_export_db = QAction("DB...", self)
        act_export_db.triggered.connect(self._on_export_db)
        menu_export.addAction(act_export_db)
        act_export_zip = QAction("Backup completo (.zip)...", self)
        act_export_zip.triggered.connect(self._on_export_zip)
        menu_export.addAction(act_export_zip)

        menu_herramientas = menubar.addMenu("Herramientas")
        act_pdf = QAction("Abrir como PDF", self)
        act_pdf.triggered.connect(self._on_generate_pdf)
        menu_herramientas.addAction(act_pdf)
        act_duplicate = QAction("Duplicar Paciente", self)
        act_duplicate.triggered.connect(self._on_duplicate_patient)
        menu_herramientas.addAction(act_duplicate)
        menu_herramientas.addSeparator()
        act_clear = QAction("Borrar Base de Datos", self)
        act_clear.triggered.connect(self._on_clear_database)
        menu_herramientas.addAction(act_clear)

        menu_acerca = menubar.addMenu("Acerca de")
        act_about = QAction("Acerca de HardForms", self)
        act_about.triggered.connect(self._on_about)
        menu_acerca.addAction(act_about)

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

        # Floating button bottom-right
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_new_float = QPushButton("+ Nuevo Paciente")
        self.btn_new_float.setFixedHeight(36)
        self.btn_new_float.setStyleSheet(
            "QPushButton { background-color: #2980B9; color: white; border: none; "
            "border-radius: 4px; padding: 6px 16px; font-weight: bold; font-size: 13px; }"
            "QPushButton:hover { background-color: #3498DB; }"
        )
        self.btn_new_float.clicked.connect(self._on_new_patient)
        btn_layout.addWidget(self.btn_new_float)
        layout.addLayout(btn_layout)

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

    def _on_duplicate_patient(self):
        patient_id = self._get_selected_patient_id()
        if patient_id is None:
            return
        from database.db import get_next_medical_record_number
        original = get_patient(patient_id)
        if original is None:
            return
        diagnoses = get_diagnoses_for_patient(patient_id)
        dup = Patient(
            first_name=original.first_name,
            last_name=original.last_name,
            dni=original.dni,
            birth_date=original.birth_date,
            phone=original.phone,
            email=original.email,
            address=original.address,
            medical_record_number=get_next_medical_record_number(),
            insurance=original.insurance,
            insurance_number=original.insurance_number,
            doctor=original.doctor,
            anesthesia_type=original.anesthesia_type,
            drug=original.drug,
            postop=original.postop,
            anesthesiologist=original.anesthesiologist,
            boston_scale=original.boston_scale,
            description=original.description,
        )
        new_id = insert_patient(dup)
        for d in diagnoses:
            insert_diagnosis(Diagnosis(
                patient_id=new_id, description=d.description, date=d.date
            ))
        QMessageBox.information(self, "Duplicado",
                                f"Paciente duplicado correctamente.\nNueva HC: {dup.medical_record_number}")
        self._load_patients(self.search_input.text().strip())

    def _on_export_csv(self):
        import csv
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar CSV", "pacientes.csv", "CSV (*.csv)"
        )
        if not file_path:
            return
        patients = get_all_patients()
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Apellido", "Nombre", "DNI", "Afiliado", "Afiliado Nº",
                                 "Nro. Historia", "FechaNacimiento", "Teléfono", "Email",
                                 "Domicilio", "Médico", "Anestesia", "Droga",
                                 "Postoperatorio", "Anestesiólogo", "Boston",
                                 "Informe", "Imágenes"])
                for p in patients:
                    imgs = ";".join(
                        f"{a.path}|{a.description}" for a in p.attachments
                    )
                    writer.writerow([
                        p.last_name, p.first_name, p.dni, p.insurance, p.insurance_number,
                        p.medical_record_number, p.birth_date, p.phone, p.email,
                        p.address, p.doctor, p.anesthesia_type, p.drug,
                        p.postop, p.anesthesiologist, p.boston_scale,
                        p.description, imgs,
                    ])
            QMessageBox.information(self, "Exportado",
                                    f"{len(patients)} pacientes exportados a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{e}")

    def _on_export_db(self):
        import shutil
        from database.db import DB_PATH
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar DB", "patients.db", "DB (*.db)"
        )
        if not file_path:
            return
        try:
            shutil.copy2(DB_PATH, file_path)
            QMessageBox.information(self, "Exportado",
                                    f"Base de datos copiada a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar la DB:\n{e}")

    def _on_export_zip(self):
        import zipfile
        from database.db import get_all_patients, DB_PATH

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar backup", "backup_hardforms.zip", "ZIP (*.zip)"
        )
        if not file_path:
            return
        try:
            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(DB_PATH, "patients.db")

                seen = set()
                for p in get_all_patients():
                    for a in p.attachments:
                        img_path = a.path
                        if not img_path or img_path in seen:
                            continue
                        if os.path.isfile(img_path):
                            seen.add(img_path)
                            # guardar con ruta completa sin drive letter
                            # d:\ESTUDIOS\HERNAN\foto.jpg -> images/d/ESTUDIOS/HERNAN/foto.jpg
                            normalized = img_path.replace(":", "")
                            arcname = f"images/{normalized}".replace("\\", "/")
                            zf.write(img_path, arcname)
            QMessageBox.information(
                self, "Backup creado",
                f"Backup exportado a:\n{file_path}\n\n"
                f"Incluye: patients.db + {len(seen)} imagen(es)."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el backup:\n{e}")

    def _on_import_zip(self):
        import zipfile
        from database.db import DB_PATH

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Restaurar backup", "", "ZIP (*.zip)"
        )
        if not file_path:
            return
        reply = QMessageBox.warning(
            self, "Restaurar backup",
            "¿Restaurar desde backup?\n\n"
            "Se reemplazará la base de datos actual y se extraerán las imágenes.\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.search_input.text().strip() != "BORRAR":
            QMessageBox.information(
                self, "Cancelado",
                "Escribí 'BORRAR' en el campo de búsqueda y volvé a intentar."
            )
            return

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.extract("patients.db", os.path.dirname(DB_PATH))

                img_count = 0
                for name in zf.namelist():
                    if name.startswith("images/") and not name.endswith("/"):
                        # images/d/ESTUDIOS/HERNAN/foto.jpg -> d:\ESTUDIOS\HERNAN\foto.jpg
                        rel = name[len("images/"):]
                        rest = rel.replace("/", "\\")
                        orig_path = rest[:1] + ":" + rest[1:]
                        os.makedirs(os.path.dirname(orig_path), exist_ok=True)
                        with open(orig_path, "wb") as out:
                            out.write(zf.read(name))
                        img_count += 1

            from database.db import init_db
            init_db()
            self._load_patients()
            QMessageBox.information(
                self, "Restaurado",
                f"Backup restaurado.\n"
                f"Base de datos: {DB_PATH}\n"
                f"Imágenes extraídas: {img_count}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo restaurar:\n{e}")

    def _on_about(self):
        from config.institution import INSTITUTION
        QMessageBox.about(
            self, "Acerca de HardForms",
            f"<b>HardForms</b><br><br>"
            f"<b>{INSTITUTION['name']}</b><br>"
            f"{INSTITUTION.get('address', '')}<br><br>"
            f"Versión 1.0<br>"
            f"Sistema de gestión de pacientes e informes médicos."
        )

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo a importar", "",
            "Archivos compatibles (*.mdb *.csv);;Access Database (*.mdb);;CSV (*.csv)"
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".mdb":
            reply = QMessageBox.question(
                self, "Importar",
                "¿Importar pacientes desde archivo .mdb?\n"
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
        elif ext == ".csv":
            self._on_import_csv(file_path)
        else:
            QMessageBox.warning(self, "Formato no soportado",
                                "Seleccioná un archivo .mdb o .csv.")

    def _on_import_csv(self, file_path: str | None = None):
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Importar CSV", "", "CSV (*.csv)"
            )
            if not file_path:
                return
        import csv
        from models.patient import ImageAttachment
        from database.db import get_next_medical_record_number

        count = 0
        try:
            with open(file_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    first = (row.get("Nombre") or "").strip()
                    last = (row.get("Apellido") or "").strip()
                    if not first or not last:
                        continue

                    # Parse imágenes
                    attachments = []
                    imgs_raw = (row.get("Imágenes") or "").strip()
                    if imgs_raw:
                        for part in imgs_raw.split(";"):
                            part = part.strip()
                            if "|" in part:
                                path, desc = part.split("|", 1)
                                attachments.append(ImageAttachment(path=path.strip(), description=desc.strip()))
                            elif part:
                                attachments.append(ImageAttachment(path=part))

                    p = Patient(
                        first_name=first, last_name=last,
                        dni=(row.get("DNI") or "").strip(),
                        birth_date=(row.get("FechaNacimiento") or "").strip(),
                        phone=(row.get("Teléfono") or "").strip(),
                        email=(row.get("Email") or "").strip(),
                        address=(row.get("Domicilio") or "").strip(),
                        medical_record_number=get_next_medical_record_number(),
                        insurance=(row.get("Afiliado") or "").strip(),
                        insurance_number=(row.get("Afiliado Nº") or "").strip(),
                        doctor=(row.get("Médico") or "").strip(),
                        anesthesia_type=(row.get("Anestesia") or "").strip(),
                        drug=(row.get("Droga") or "").strip(),
                        postop=(row.get("Postoperatorio") or "").strip(),
                        anesthesiologist=(row.get("Anestesiólogo") or "").strip(),
                        boston_scale=(row.get("Boston") or "").strip(),
                        description=(row.get("Informe") or "").strip(),
                        attachments=attachments,
                    )
                    insert_patient(p)
                    count += 1
            QMessageBox.information(self, "Importado", f"{count} pacientes importados.")
            self._load_patients(self.search_input.text().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar CSV:\n{e}")

    def _on_clear_database(self):
        reply = QMessageBox.warning(
            self, "Borrar Base de Datos",
            "¿Estás seguro de que querés borrar TODOS los pacientes, diagnósticos y "
            "datos de la base de datos?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.search_input.text().strip() != "BORRAR":
            QMessageBox.information(
                self, "Confirmación requerida",
                "Escribí 'BORRAR' (mayúsculas) en el campo de búsqueda y "
                "volvé a hacer clic en 'Borrar Base de Datos'."
            )
            return
        from database.db import clear_all_data
        clear_all_data()
        self.search_input.clear()
        self._load_patients()
        QMessageBox.information(self, "Base de datos borrada",
                                "Todos los datos fueron eliminados.")

    def _on_generate_pdf(self):
        patient_id = self._get_selected_patient_id()
        if patient_id is None:
            return

        patient = get_patient(patient_id)
        if patient is None:
            return

        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        try:
            generate_patient_report(patient_id, tmp.name)
            QDesktopServices.openUrl(QUrl.fromLocalFile(tmp.name))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el informe:\n{e}")
