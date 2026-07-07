from dataclasses import dataclass, field
from typing import List


@dataclass
class ImageAttachment:
    path: str = ""
    description: str = ""


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
    insurance: str = ""
    insurance_number: str = ""
    description: str = ""
    attachments: List[ImageAttachment] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_study_date: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.last_name}, {self.first_name}"
