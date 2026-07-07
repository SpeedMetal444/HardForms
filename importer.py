import csv
import os
import subprocess
import sys
from datetime import datetime, timedelta

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MDB_PATH = os.path.join(CURRENT_DIR, "BaseInformes.mdb")
VBS_PATH = os.path.join(CURRENT_DIR, "export_table.vbs")
SYSWOW64_CS = r"C:\Windows\SysWOW64\cscript.exe"

sys.path.insert(0, CURRENT_DIR)
from database.db import get_connection
from models.patient import Patient
from models.diagnosis import Diagnosis


def parse_date(val):
    if not val:
        return ""
    val = val.strip().strip('"')
    if not val:
        return ""
    try:
        n = float(val)
        if n > 10000:
            base = datetime(1899, 12, 30)
            d = base + timedelta(days=n)
            return d.strftime("%d/%m/%Y")
    except ValueError:
        pass
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"]:
        try:
            return datetime.strptime(val, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return val


def parse_name(full):
    full = full.strip().strip('"')
    if not full:
        return "", ""
    parts = full.split(None, 1)
    if len(parts) == 2:
        return parts[0].upper(), parts[1].title()
    return (parts[0].upper(), "") if parts else ("", "")


def export_mdb_to_csv(table_name, csv_path, mdb_path):
    export_vbs = os.path.join(CURRENT_DIR, "export_table.vbs")
    if not os.path.isfile(export_vbs):
        raise FileNotFoundError(f"No se encuentra {export_vbs}")

    cscript = r"C:\Windows\SysWOW64\cscript.exe"
    if not os.path.isfile(cscript):
        cscript = "cscript.exe"

    result = subprocess.run(
        [cscript, "//Nologo", export_vbs, table_name, csv_path, mdb_path],
        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or "Error desconocido"
        raise RuntimeError(f"Error exportando {table_name}: {detail}")


def bulk_insert(conn, patients_with_diagnoses):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cur = conn.cursor()
    for p, diagnoses in patients_with_diagnoses:
        cur.execute("""
            INSERT INTO patients (first_name, last_name, dni, birth_date, phone, email,
                                  address, medical_record_number, description, attachments,
                                  created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p.first_name, p.last_name, p.dni, p.birth_date, p.phone, p.email,
              p.address, p.medical_record_number, p.description, "", now, now))
        pid = cur.lastrowid
        for d in diagnoses:
            d.patient_id = pid
            cur.execute("""
                INSERT INTO diagnoses (patient_id, description, date)
                VALUES (?, ?, ?)
            """, (d.patient_id, d.description, d.date))
    conn.commit()


def import_estudios(csv_path, conn, progress=None):
    count = 0
    batch = []
    with open(csv_path, encoding="cp1252") as f:
        reader = csv.DictReader(f)
        for row in reader:
            paciente = (row.get("Paciente") or "").strip()
            if not paciente:
                continue
            last_name, first_name = parse_name(paciente)
            birth_date = parse_date(row.get("FecNacimiento", ""))
            indicacion = (row.get("Indicacion") or "").strip()
            fecha = parse_date(row.get("FecEstudio", ""))

            sections = []
            for campo in ["Esofago", "Estomago", "Duodeno", "Colonoscopia",
                          "AnoscopiaExterna", "TactoRectal", "AnoscopiaInterna",
                          "InformeRecto", "Informe"]:
                val = (row.get(campo) or "").strip()
                if val:
                    sections.append(f"{campo}: {val}")
            description = "\n\n".join(sections)

            p = Patient(
                first_name=first_name,
                last_name=last_name or paciente[:50],
                dni=(row.get("AfiliadoNro") or "").strip(),
                birth_date=birth_date,
                description=description,
            )

            diagnoses = []
            seen = set()
            for c in ["Conclusiones1", "Conclusiones2", "Conclusiones3"]:
                val = (row.get(c) or "").strip()
                if val and val not in seen:
                    seen.add(val)
                    diagnoses.append(Diagnosis(description=val, date=fecha))

            if indicacion and indicacion not in seen:
                diagnoses.append(Diagnosis(description=indicacion, date=fecha))

            batch.append((p, diagnoses))
            count += 1
            if len(batch) >= 500:
                bulk_insert(conn, batch)
                if progress:
                    progress(count)
                batch = []

    if batch:
        bulk_insert(conn, batch)
    if progress:
        progress(count)
    return count


def import_ecografias(csv_path, conn, progress=None):
    count = 0
    batch = []
    with open(csv_path, encoding="cp1252") as f:
        reader = csv.DictReader(f)
        for row in reader:
            paciente = (row.get("Paciente") or "").strip()
            if not paciente:
                continue
            last_name, first_name = parse_name(paciente)
            birth_date = parse_date(row.get("FecNacimiento", ""))
            indicacion = (row.get("Indicacion") or "").strip()
            fecha = parse_date(row.get("FecEstudio", ""))
            informe = (row.get("Informe") or "").strip()
            tipo = (row.get("TipoEcografia") or "").strip()

            description = informe
            if tipo:
                description = f"Tipo: {tipo}\n\n{description}"

            p = Patient(
                first_name=first_name,
                last_name=last_name or paciente[:50],
                dni=(row.get("AfiliadoNro") or "").strip(),
                birth_date=birth_date,
                description=description,
            )

            diagnoses = []
            if indicacion:
                diagnoses.append(Diagnosis(description=indicacion, date=fecha))

            batch.append((p, diagnoses))
            count += 1
            if len(batch) >= 500:
                bulk_insert(conn, batch)
                if progress:
                    progress(count)
                batch = []

    if batch:
        bulk_insert(conn, batch)
    if progress:
        progress(count)
    return count


def clean_old_records(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM diagnoses")
    cur.execute("DELETE FROM patients")
    conn.commit()


def run_import(mdb_path=None, progress=None):
    """
    Exporta MDB a CSV via VBS y luego importa a SQLite.
    mdb_path: ruta al archivo .mdb. Si es None, usa BaseInformes.mdb del directorio actual.
    progress: callable(msg) para reportar avance desde la UI.
    Retorna (estudios_count, ecografias_count).
    """
    from database.db import init_db
    init_db()

    path = mdb_path or MDB_PATH
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No se encuentra el archivo: {path}")

    conn = get_connection()
    tmp = os.environ["TEMP"]
    csv_est = None
    csv_eco = None

    try:
        # Limpiar datos previos
        if progress:
            progress("Limpiando registros anteriores...")
        clean_old_records(conn)

        # Exportar Estudios
        csv_est = os.path.join(tmp, "Estudios.csv")
        if progress:
            progress("Exportando tabla Estudios...")
        export_mdb_to_csv("Estudios", csv_est, path)

        if progress:
            progress("Importando Estudios...")
        n_est = import_estudios(csv_est, conn, progress=lambda c: progress(f"Importando Estudios... {c} pacientes"))

        # Exportar Ecografias
        csv_eco = os.path.join(tmp, "Ecografias.csv")
        if progress:
            progress("Exportando tabla Ecografias...")
        export_mdb_to_csv("Ecografias", csv_eco, path)

        if progress:
            progress("Importando Ecografias...")
        n_eco = import_ecografias(csv_eco, conn, progress=lambda c: progress(f"Importando Ecografias... {c} pacientes"))

        return n_est, n_eco

    finally:
        conn.close()
        for f in [csv_est, csv_eco]:
            if f:
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                except Exception:
                    pass
