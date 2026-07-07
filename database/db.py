import sqlite3
import os
from models.patient import Patient, ImageAttachment
from models.diagnosis import Diagnosis
from typing import List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "patients.db")

IMG_SEP = "|||"


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dni TEXT,
            birth_date TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            medical_record_number TEXT,
            description TEXT,
            attachments TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            date TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)
    # Migration: old column name
    try:
        conn.execute("ALTER TABLE patients RENAME COLUMN image_paths TO attachments")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE diagnoses DROP COLUMN icd10_code")
    except Exception:
        pass
    conn.commit()
    conn.close()


def insert_patient(p: Patient) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO patients (first_name, last_name, dni, birth_date, phone, email,
                              address, medical_record_number, description, attachments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (p.first_name, p.last_name, p.dni, p.birth_date, p.phone, p.email,
          p.address, p.medical_record_number, p.description,
          _attachments_to_str(p.attachments)))
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_patient(p: Patient):
    conn = get_connection()
    conn.execute("""
        UPDATE patients SET first_name=?, last_name=?, dni=?, birth_date=?, phone=?,
                            email=?, address=?, medical_record_number=?, description=?,
                            attachments=?, updated_at=datetime('now','localtime')
        WHERE id=?
    """, (p.first_name, p.last_name, p.dni, p.birth_date, p.phone, p.email,
          p.address, p.medical_record_number, p.description,
          _attachments_to_str(p.attachments), p.id))
    conn.commit()
    conn.close()


def delete_patient(patient_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
    conn.commit()
    conn.close()


def get_patient(patient_id: int) -> Patient | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_patient(row)


def get_all_patients() -> List[Patient]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM patients ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [_row_to_patient(r) for r in rows]


def search_patients(query: str) -> List[Patient]:
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute("""
        SELECT * FROM patients
        WHERE first_name LIKE ? OR last_name LIKE ? OR dni LIKE ?
        ORDER BY updated_at DESC
    """, (like, like, like)).fetchall()
    conn.close()
    return [_row_to_patient(r) for r in rows]


def _attachments_to_str(attachments: List[ImageAttachment]) -> str:
    return "\n".join(
        f"{a.path}{IMG_SEP}{a.description}" for a in attachments
    )


def _str_to_attachments(raw: str) -> List[ImageAttachment]:
    result = []
    for line in (raw or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        if IMG_SEP in line:
            path, desc = line.split(IMG_SEP, 1)
        else:
            path, desc = line, ""  # legacy format
        result.append(ImageAttachment(path=path, description=desc))
    return result


def _row_to_patient(row: sqlite3.Row) -> Patient:
    return Patient(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        dni=row["dni"],
        birth_date=row["birth_date"],
        phone=row["phone"],
        email=row["email"],
        address=row["address"],
        medical_record_number=row["medical_record_number"],
        description=row["description"],
        attachments=_str_to_attachments(row["attachments"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# --- Diagnoses CRUD ---

def insert_diagnosis(d: Diagnosis) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO diagnoses (patient_id, description, date)
        VALUES (?, ?, ?)
    """, (d.patient_id, d.description, d.date))
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_diagnosis(d: Diagnosis):
    conn = get_connection()
    conn.execute("""
        UPDATE diagnoses SET description=?, date=?
        WHERE id=?
    """, (d.description, d.date, d.id))
    conn.commit()
    conn.close()


def delete_diagnosis(diagnosis_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM diagnoses WHERE id=?", (diagnosis_id,))
    conn.commit()
    conn.close()


def get_diagnoses_for_patient(patient_id: int) -> List[Diagnosis]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM diagnoses WHERE patient_id=? ORDER BY date DESC, id DESC",
        (patient_id,)
    ).fetchall()
    conn.close()
    return [_row_to_diagnosis(r) for r in rows]


def delete_diagnoses_for_patient(patient_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM diagnoses WHERE patient_id=?", (patient_id,))
    conn.commit()
    conn.close()


def _row_to_diagnosis(row: sqlite3.Row) -> Diagnosis:
    return Diagnosis(
        id=row["id"],
        patient_id=row["patient_id"],
        description=row["description"],
        date=row["date"],
    )
