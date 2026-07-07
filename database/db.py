import sqlite3
import os
from models.patient import Patient
from typing import List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "patients.db")


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
            image_paths TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.commit()
    conn.close()


def insert_patient(p: Patient) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO patients (first_name, last_name, dni, birth_date, phone, email,
                              address, medical_record_number, description, image_paths)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (p.first_name, p.last_name, p.dni, p.birth_date, p.phone, p.email,
          p.address, p.medical_record_number, p.description,
          "\n".join(p.image_paths)))
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_patient(p: Patient):
    conn = get_connection()
    conn.execute("""
        UPDATE patients SET first_name=?, last_name=?, dni=?, birth_date=?, phone=?,
                            email=?, address=?, medical_record_number=?, description=?,
                            image_paths=?, updated_at=datetime('now','localtime')
        WHERE id=?
    """, (p.first_name, p.last_name, p.dni, p.birth_date, p.phone, p.email,
          p.address, p.medical_record_number, p.description,
          "\n".join(p.image_paths), p.id))
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
        image_paths=[p for p in (row["image_paths"] or "").split("\n") if p],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
