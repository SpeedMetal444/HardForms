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
    try:
        conn.execute("ALTER TABLE patients ADD COLUMN insurance TEXT")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE patients ADD COLUMN insurance_number TEXT")
    except Exception:
        pass
    for col in ["doctor", "anesthesia_type", "drug", "postop", "anesthesiologist", "boston_scale"]:
        try:
            conn.execute(f"ALTER TABLE patients ADD COLUMN {col} TEXT")
        except Exception:
            pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lookup_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_type TEXT NOT NULL,
            value TEXT NOT NULL,
            UNIQUE(list_type, value)
        )
    """)
    conn.commit()
    conn.close()


def get_next_medical_record_number() -> str:
    conn = get_connection()
    row = conn.execute("SELECT MAX(CAST(medical_record_number AS INTEGER)) FROM patients").fetchone()
    conn.close()
    last = row[0] or 0
    return f"HC-{last + 1:05d}"


PATIENT_COLS = (
    "first_name, last_name, dni, birth_date, phone, email, "
    "address, medical_record_number, insurance, insurance_number, "
    "doctor, anesthesia_type, drug, postop, anesthesiologist, boston_scale, "
    "description, attachments"
)
PATIENT_PLACEHOLDERS = ", ".join("?" for _ in range(18))


def insert_patient(p: Patient) -> int:
    conn = get_connection()
    cur = conn.execute(f"""
        INSERT INTO patients ({PATIENT_COLS})
        VALUES ({PATIENT_PLACEHOLDERS})
    """, (p.first_name, p.last_name, p.dni, p.birth_date, p.phone, p.email,
          p.address, p.medical_record_number, p.insurance, p.insurance_number,
          p.doctor, p.anesthesia_type, p.drug, p.postop, p.anesthesiologist, p.boston_scale,
          p.description, _attachments_to_str(p.attachments)))
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_patient(p: Patient):
    conn = get_connection()
    conn.execute(f"""
        UPDATE patients SET first_name=?, last_name=?, dni=?, birth_date=?, phone=?,
                            email=?, address=?, medical_record_number=?,
                            insurance=?, insurance_number=?,
                            doctor=?, anesthesia_type=?, drug=?, postop=?,
                            anesthesiologist=?, boston_scale=?,
                            description=?, attachments=?,
                            updated_at=datetime('now','localtime')
        WHERE id=?
    """, (p.first_name, p.last_name, p.dni, p.birth_date, p.phone, p.email,
          p.address, p.medical_record_number, p.insurance, p.insurance_number,
          p.doctor, p.anesthesia_type, p.drug, p.postop, p.anesthesiologist, p.boston_scale,
          p.description, _attachments_to_str(p.attachments), p.id))
    conn.commit()
    conn.close()


def delete_patient(patient_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
    conn.commit()
    conn.close()


def get_patient(patient_id: int) -> Patient | None:
    conn = get_connection()
    row = conn.execute(PATIENTS_SQL + " WHERE p.id=?", (patient_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_patient(row)


def _date_sort(col):
    """Convierte columna DD/MM/AAAA a texto ordenable AAAA/MM/DD."""
    return f"SUBSTR({col}, 7, 4) || SUBSTR({col}, 4, 2) || SUBSTR({col}, 1, 2)"


PATIENTS_SQL = """
    SELECT p.*, (
        SELECT d.date FROM diagnoses d
        WHERE d.patient_id = p.id
        ORDER BY d.date DESC, d.id DESC LIMIT 1
    ) AS last_study_date
    FROM patients p
"""

SORT_EXPR = f"COALESCE({_date_sort('last_study_date')}, '')"


def get_all_patients() -> List[Patient]:
    conn = get_connection()
    rows = conn.execute(PATIENTS_SQL + f" ORDER BY {SORT_EXPR} DESC, p.updated_at DESC").fetchall()
    conn.close()
    return [_row_to_patient(r) for r in rows]


def search_patients(query: str) -> List[Patient]:
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(PATIENTS_SQL + f"""
        WHERE p.first_name LIKE ? OR p.last_name LIKE ? OR p.dni LIKE ?
           OR p.insurance LIKE ? OR p.insurance_number LIKE ?
        ORDER BY {SORT_EXPR} DESC, p.updated_at DESC
    """, (like, like, like, like, like)).fetchall()
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
        insurance=row["insurance"] or "",
        insurance_number=row["insurance_number"] or "",
        doctor=row["doctor"] or "",
        anesthesia_type=row["anesthesia_type"] or "",
        drug=row["drug"] or "",
        postop=row["postop"] or "",
        anesthesiologist=row["anesthesiologist"] or "",
        boston_scale=row["boston_scale"] or "",
        description=row["description"],
        attachments=_str_to_attachments(row["attachments"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_study_date=row["last_study_date"] or "",
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


# --- Lookup lists ---

def get_lookup_list(list_type: str) -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT value FROM lookup_lists WHERE list_type=? ORDER BY value",
        (list_type,)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def add_lookup_value(list_type: str, value: str):
    if not value.strip():
        return
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO lookup_lists (list_type, value) VALUES (?, ?)",
            (list_type, value.strip())
        )
        conn.commit()
    finally:
        conn.close()


def _row_to_diagnosis(row: sqlite3.Row) -> Diagnosis:
    return Diagnosis(
        id=row["id"],
        patient_id=row["patient_id"],
        description=row["description"],
        date=row["date"],
    )
