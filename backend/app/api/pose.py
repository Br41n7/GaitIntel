"""
Pose extraction endpoint — Phase 2 of the build order.

Runs extraction as a background task rather than synchronously in the
request. This matters more than it might look: MediaPipe extraction is
CPU-bound and holds every frame's landmarks in memory, and on
constrained hosting (e.g. Render's free tier: 0.1 vCPU, 512MB RAM) a
synchronous in-request version can take minutes or get OOM-killed
mid-request — which leaves the assessment stuck at `pose_extracting`
forever with no way to tell the difference between "still working" and
"silently died." Returning immediately and having the frontend poll
`GET /api/assessments/{id}` for status changes avoids both problems:
the request always completes fast, and a crash mid-task still lands on
`failed` with an error message (a bare exception during a background
task, before this function's own try/except, is one edge case this
doesn't cover — see the note in DEPLOY.md about the resource cap).
"""
import logging
import uuid
from dataclasses import asdict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.models.assessment import Assessment, AssessmentStatus
from app.pose.mediapipe_provider import MediaPipePoseProvider
from app.schemas.assessment import AssessmentOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pose", tags=["pose"])

POSE_PROVIDER_VERSION = "mediapipe-0.1.0"


def _extract_pose_background(assessment_id: uuid.UUID, video_path: str) -> None:
    """Runs in a background thread after the triggering request has
    already returned — needs its own DB session, since the request-scoped
    one from `get_db()` is closed by the time this executes."""
    db = SessionLocal()
    try:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            logger.error("Assessment %s vanished before background pose extraction ran", assessment_id)
            return

        provider = MediaPipePoseProvider()
        try:
            frames = provider.extract(video_path)
        except Exception as e:
            logger.exception("Pose extraction failed for assessment %s", assessment_id)
            assessment.status = AssessmentStatus.failed
            assessment.error_message = f"Pose extraction failed: {e}"
            db.commit()
            return

        assessment.pose_data = {
            "provider_version": POSE_PROVIDER_VERSION,
            "frame_count": len(frames),
            "frames": [asdict(f) for f in frames],
        }
        assessment.status = AssessmentStatus.pose_extracted
        assessment.error_message = None
        db.commit()
    finally:
        db.close()


@router.post("/{assessment_id}/extract", response_model=AssessmentOut)
def extract_pose(assessment_id: uuid.UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.video_path:
        raise HTTPException(status_code=400, detail="Upload a video before extracting pose")

    assessment.status = AssessmentStatus.pose_extracting
    assessment.error_message = None
    db.commit()

    background_tasks.add_task(_extract_pose_background, assessment_id, assessment.video_path)

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
