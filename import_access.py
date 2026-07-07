"""
Importador de BaseInformes.mdb (Access 97) a HardForms SQLite.
"""

import os
import csv
import subprocess
import tempfile
from datetime import datetime, timedelta
from database.db import init_db, insert_patient, insert_diagnosis
from models.patient import Patient, ImageAttachment
from models.diagnosis import Diagnosis

MDB_DIR = os.path.dirname(os.path.abspath(__file__))
MDB_PATH = os.path.join(MDB_DIR, "BaseInformes.mdb")
VBS_PATH = os.path.join(MDB_DIR, "export_table.vbs")
DATA_DIR = os.path.join(MDB_DIR, "data")


def vbs_export(table, output_csv):
    subprocess.run(
        [r"C:\Windows\SysWOW64\cscript.exe", "//NoLogo", VBS_PATH, table, output_csv],
        capture_output=True, timeout=120
    )


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
    return parts[0].upper() if parts else ("", "")


def import_estudios():
    csv_path = os.path.join(tempfile.gettempdir(), "Estudios.csv")
    print("Exportando Estudios...")
    vbs_export("Estudios", csv_path)

    count = 0
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

            attachments = []
            for i in range(3):
                foto = (row.get(f"ArcFoto{i}") or "").strip()
                comentario = (row.get(f"ComentarioFoto{i}") or "").strip()
                path = os.path.join(MDB_DIR, foto) if foto and not os.path.isabs(foto) else foto
                if path and os.path.isfile(path):
                    attachments.append(ImageAttachment(path=path, description=comentario))

            p = Patient(
                first_name=first_name,
                last_name=last_name or paciente[:50],
                dni=(row.get("AfiliadoNro") or "").strip(),
                birth_date=birth_date,
                description=description,
                attachments=attachments,
            )
            pid = insert_patient(p)

            seen = set()
            for c in ["Conclusiones1", "Conclusiones2", "Conclusiones3"]:
                val = (row.get(c) or "").strip()
                if val and val not in seen:
                    seen.add(val)
                    insert_diagnosis(Diagnosis(patient_id=pid, description=val, date=fecha))

            if indicacion and indicacion not in seen:
                insert_diagnosis(Diagnosis(patient_id=pid, description=indicacion, date=fecha))

            count += 1

    os.remove(csv_path)
    print(f"  -> {count} pacientes desde Estudios")
    return count


def import_ecografias():
    csv_path = os.path.join(tempfile.gettempdir(), "Ecografias.csv")
    print("Exportando Ecografias...")
    vbs_export("Ecografias", csv_path)

    count = 0
    with open(csv_path, encoding="cp1252") as f:
        reader = csv.DictReader(f)
        for row in reader:
            paciente = (row.get("Paciente") or "").strip()
            if not paciente:
                continue

            last_name, first_name = parse_name(paciente)
            birth_date = parse_date(row.get("FecNacimiento", ""))
            informe = (row.get("Informe") or "").strip()
            indicacion = (row.get("Indicacion") or "").strip()
            fecha = parse_date(row.get("FecEstudio", ""))
            tipo = (row.get("TipoEcografia") or "").strip()

            description = informe
            if tipo:
                description = f"Tipo: {tipo}\n\n{description}"

            attachments = []
            for i in range(1, 5):
                foto = (row.get(f"ArcFoto{i}") or "").strip()
                path = os.path.join(MDB_DIR, foto) if foto and not os.path.isabs(foto) else foto
                if path and os.path.isfile(path):
                    attachments.append(ImageAttachment(path=path, description=""))

            p = Patient(
                first_name=first_name,
                last_name=last_name or paciente[:50],
                dni=(row.get("AfiliadoNro") or "").strip(),
                birth_date=birth_date,
                description=description,
                attachments=attachments,
            )
            pid = insert_patient(p)

            if indicacion:
                insert_diagnosis(Diagnosis(patient_id=pid, description=indicacion, date=fecha))

            count += 1

    os.remove(csv_path)
    print(f"  -> {count} pacientes desde Ecografias")
    return count


def main():
    init_db()
    total = import_estudios() + import_ecografias()
    print(f"\nImportacion completa: {total} pacientes.")


if __name__ == "__main__":
    main()
