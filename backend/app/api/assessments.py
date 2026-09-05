import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assessment import Assessment, AssessmentStatus
from app.pipeline.video_validation import VideoValidationError, validate_video
from app.pose.mediapipe_provider import read_video_metadata
from app.schemas.assessment import AssessmentCreate, AssessmentNotesUpdate, AssessmentOut
from app.storage.local import get_storage_backend

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.get("", response_model=list[AssessmentOut])
def list_assessments(patient_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    query = db.query(Assessment)
    if patient_id:
        query = query.filter(Assessment.patient_id == patient_id)
    return query.order_by(Assessment.created_at.desc()).all()


@router.post("", response_model=AssessmentOut, status_code=201)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    assessment = Assessment(patient_id=payload.patient_id, status=AssessmentStatus.created)
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.post("/{assessment_id}/video", response_model=AssessmentOut)
def upload_video(assessment_id: uuid.UUID, file: UploadFile, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    allowed_extensions = (".mp4", ".mov", ".avi", ".webm")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail=f"Unsupported video format: {file.filename}")

    storage = get_storage_backend()
    key = f"{assessment_id}/{file.filename}"
    saved_path = storage.save(key, file.file)

    try:
        validate_video(saved_path)
        metadata = read_video_metadata(saved_path)
    except VideoValidationError as e:
        assessment.status = AssessmentStatus.failed
        db.commit()
        raise HTTPException(status_code=400, detail=str(e)) from e

    assessment.video_path = saved_path
    assessment.video_storage_key = key
    assessment.video_original_filename = file.filename
    assessment.video_fps = metadata.fps
    assessment.video_duration_s = metadata.duration_s
    assessment.video_width = metadata.width
    assessment.video_height = metadata.height
    assessment.status = AssessmentStatus.video_uploaded
    db.commit()
    db.refresh(assessment)
    return assessment


@router.patch("/{assessment_id}/notes", response_model=AssessmentOut)
def update_notes(assessment_id: uuid.UUID, payload: AssessmentNotesUpdate, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    assessment.clinician_notes = payload.clinician_notes
    db.commit()
    db.refresh(assessment)
    return assessment
