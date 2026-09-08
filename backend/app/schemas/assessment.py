import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.assessment import AssessmentStatus


class AssessmentCreate(BaseModel):
    patient_id: uuid.UUID


class AssessmentNotesUpdate(BaseModel):
    clinician_notes: str


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    status: AssessmentStatus
    video_original_filename: str | None = None
    video_storage_key: str | None = None
    video_fps: float | None = None
    video_duration_s: float | None = None
    video_width: int | None = None
    video_height: int | None = None
    results: dict[str, Any] | None = None
    clinician_notes: str | None = None
    error_message: str | None = None
    analysis_version: str | None = None
    knowledge_version: str | None = None
    created_at: datetime
    updated_at: datetime
