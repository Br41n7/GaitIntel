import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class AssessmentStatus(str, enum.Enum):
    created = "created"
    video_uploaded = "video_uploaded"
    pose_extracting = "pose_extracting"
    pose_extracted = "pose_extracted"
    analyzing = "analyzing"
    analyzed = "analyzed"
    reviewed = "reviewed"
    failed = "failed"


class Assessment(Base):
    """
    One gait assessment: one video, one analysis run, one clinician
    review. `results` holds the pipeline output (GaitMetrics + findings)
    as JSON for v0.1 — see app/pipeline/gait_types.py for the shape. This
    moves to proper normalized tables once the shape has stabilized
    against real usage; premature normalization here would just mean
    migrating twice.
    """
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.created, nullable=False)

    video_path = Column(String, nullable=True)  # full filesystem path, for backend use
    video_storage_key = Column(String, nullable=True)  # relative key, used to build the /media URL
    video_original_filename = Column(String, nullable=True)
    video_fps = Column(Float, nullable=True)
    video_duration_s = Column(Float, nullable=True)
    video_width = Column(Integer, nullable=True)
    video_height = Column(Integer, nullable=True)

    # Phase 2: raw (smoothed) pose landmarks, one entry per frame — see
    # app/pose/mediapipe_provider.py. Stored as JSON for v0.1; moves to
    # a dedicated table or object storage once files get large enough
    # that loading the whole assessment row to read pose data is wasteful.
    pose_data = Column(JSON, nullable=True)

    results = Column(JSON, nullable=True)  # GaitMetrics + findings, see pipeline/gait_types.py
    clinician_notes = Column(Text, nullable=True)

    analysis_version = Column(String, nullable=True)
    knowledge_version = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient")
