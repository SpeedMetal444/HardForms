from dataclasses import dataclass


@dataclass
class Diagnosis:
    id: int | None = None
    patient_id: int = 0
    description: str = ""
    date: str = ""
