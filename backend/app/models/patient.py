import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class Patient(Base):
    """
    Minimal patient record for v0.1. No PHI beyond what a clinician
    needs to tell patients apart and track assessments over time —
    this is a clinical tool, not a records system, and should stay
    that way until there's a real reason to expand it.
    """
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String, unique=True, nullable=False)  # clinic-assigned ID, not a name
    display_name = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
