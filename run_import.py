"""Runner para importar los CSVs ya exportados a SQLite."""
import csv
import os
import sys
import sqlite3
sys.path.insert(0, os.path.dirname(__file__))

from database.db import get_connection
from models.patient import Patient
from models.diagnosis import Diagnosis
from datetime import datetime, timedelta


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


def bulk_insert(conn, patients_with_diagnoses):
    """Inserta pacientes y diagnósticos en batch usando una sola conexión."""
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


def import_estudios(csv_path, conn):
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
                print(f"  {count}...")
                batch = []

    if batch:
        bulk_insert(conn, batch)
    return count


def import_ecografias(csv_path, conn):
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
                print(f"  eco {count}...")
                batch = []

    if batch:
        bulk_insert(conn, batch)
    return count


def main():
    from database.db import init_db
    init_db()

    conn = get_connection()
    tmp = os.environ["TEMP"]

    csv_est = os.path.join(tmp, "Estudios.csv")
    if os.path.isfile(csv_est):
        print("Importando Estudios...")
        n = import_estudios(csv_est, conn)
        print(f"  -> {n} pacientes")
    else:
        print("Estudios.csv no encontrado")

    csv_eco = os.path.join(tmp, "Ecografias.csv")
    if os.path.isfile(csv_eco):
        print("Importando Ecografias...")
        n = import_ecografias(csv_eco, conn)
        print(f"  -> {n} pacientes")

    conn.close()
    print("Importacion completada.")


if __name__ == "__main__":
    main()
