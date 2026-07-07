from dataclasses import dataclass


@dataclass
class Diagnosis:
    id: int | None = None
    patient_id: int = 0
    icd10_code: str = ""
    description: str = ""
    date: str = ""
