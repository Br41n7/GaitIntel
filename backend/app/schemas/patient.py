import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PatientBase(BaseModel):
    identifier: str
    display_name: str | None = None
    date_of_birth: datetime | None = None
    notes: str | None = None


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
