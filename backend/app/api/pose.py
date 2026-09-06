"""
Pose extraction endpoint — Phase 2 of the build order.

Separate from analysis.py on purpose: pose extraction (video -> raw
landmarks) and gait analysis (landmarks -> metrics/findings) are
different pipeline stages with different failure modes and runtimes.
Once Phase 3/4 land, `analysis.py`'s real (non-stub) implementation
will read from `assessment.pose_data` that this endpoint produces —
this route doesn't change when that happens.
"""
import logging
import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assessment import Assessment, AssessmentStatus
from app.pose.mediapipe_provider import MediaPipePoseProvider
from app.schemas.assessment import AssessmentOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pose", tags=["pose"])

POSE_PROVIDER_VERSION = "mediapipe-0.1.0"


@router.post("/{assessment_id}/extract", response_model=AssessmentOut)
def extract_pose(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.video_path:
        raise HTTPException(status_code=400, detail="Upload a video before extracting pose")

    assessment.status = AssessmentStatus.pose_extracting
    db.commit()

    provider = MediaPipePoseProvider()
    try:
        frames = provider.extract(assessment.video_path)
    except Exception as e:
        logger.exception("Pose extraction failed for assessment %s", assessment_id)
        assessment.status = AssessmentStatus.failed
        db.commit()
        raise HTTPException(status_code=500, detail=f"Pose extraction failed: {e}") from e

    # Stored as plain JSON for v0.1 — see the note on Assessment.pose_data.
    assessment.pose_data = {
        "provider_version": POSE_PROVIDER_VERSION,
        "frame_count": len(frames),
        "frames": [asdict(f) for f in frames],
    }
    assessment.status = AssessmentStatus.pose_extracted
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/{assessment_id}")
def get_pose_data(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.pose_data:
        raise HTTPException(status_code=404, detail="No pose data yet — run extraction first")
    return assessment.pose_data
