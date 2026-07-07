from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class Patient:
    id: int | None = None
    first_name: str = ""
    last_name: str = ""
    dni: str = ""
    birth_date: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    medical_record_number: str = ""
    description: str = ""
    image_paths: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.last_name}, {self.first_name}"
