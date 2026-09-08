"""
Analysis trigger endpoint.

Phase 3 (this version): real joint-angle calculation, gait-cycle
segmentation, and gait metrics — computed from the pose data already
extracted (see app/api/pose.py). See app/gait/pipeline.py for the
actual computation.

Deviation detection (the 10 deterministic rules, Phase 4) is NOT
implemented yet. Rather than mixing real metrics with fake findings in
the same response — which would be more misleading than an all-stub
response, since there'd be no way to tell which half is real — the
`findings` field is explicitly empty with a status message until
Phase 4 lands.
"""
import logging
import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.gait.pipeline import GaitAnalysisError, run_gait_analysis
from app.models.assessment import Assessment, AssessmentStatus
from app.schemas.assessment import AssessmentOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

ANALYSIS_VERSION = "0.3.0"  # Phase 3: real metrics, findings still Phase 4


@router.post("/{assessment_id}/run", response_model=AssessmentOut)
def run_analysis(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.pose_data:
        raise HTTPException(status_code=400, detail="Extract pose before running analysis")
    if not assessment.video_fps:
        raise HTTPException(status_code=400, detail="Missing video frame rate; re-upload the video")

    assessment.status = AssessmentStatus.analyzing
    db.commit()

    try:
        gait_output = run_gait_analysis(assessment.pose_data, assessment.video_fps)
    except GaitAnalysisError as e:
        assessment.status = AssessmentStatus.failed
        assessment.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Gait analysis failed for assessment %s", assessment_id)
        assessment.status = AssessmentStatus.failed
        assessment.error_message = f"Gait analysis failed: {e}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Gait analysis failed: {e}") from e

    results = {
        "metrics": gait_output["metrics"],
        "joint_angle_trajectories": gait_output["joint_angle_trajectories"],
        "gait_cycles": gait_output["gait_cycles"],
        "events": gait_output["events"],
        "findings": [],
        "findings_status": "Deviation detection is not implemented yet (Phase 4). "
                            "Metrics above are computed from real pose data.",
        "analysis_version": ANALYSIS_VERSION,
    }

    assessment.results = results
    assessment.analysis_version = ANALYSIS_VERSION
    assessment.knowledge_version = None  # no findings yet, so no knowledge-base version to attach
    assessment.error_message = None
    assessment.status = AssessmentStatus.analyzed
    db.commit()
    db.refresh(assessment)
    return assessment
