"""
Analysis trigger endpoint.

v0.1: the CV pipeline (pose extraction, gait math, deviation
detection) doesn't exist yet — that's Phases 2-4 of the build order.
This route exists now so the frontend, DB schema, and status flow can
be built and tested against a real (if fake) response shape, instead
of everyone guessing at the contract until the pipeline is ready.

Replace `_run_stub_analysis` with a call into
`app.pipeline.pipeline.run(video_path)` once Phases 2-4 land. Nothing
else in this file — or in the frontend that consumes it — should need
to change, since the response shape is already the real one.
"""
import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.clinical.knowledge_engine import ClinicalKnowledgeEngine
from app.db.session import get_db
from app.models.assessment import Assessment, AssessmentStatus
from app.pipeline.gait_types import GaitFinding, GaitMetrics, Phase, Side
from app.schemas.assessment import AssessmentOut

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

ANALYSIS_VERSION = "0.1.0-stub"


def _run_stub_analysis() -> dict:
    """Placeholder pipeline output, shaped exactly like the real
    pipeline's eventual output (GaitMetrics + list[GaitFinding] with
    knowledge-engine results attached). No real CV happens here —
    do not mistake this for a working analyzer."""
    metrics = GaitMetrics(
        cadence_steps_per_min=102,
        left_stance_time_s=0.72,
        right_stance_time_s=0.81,
        step_asymmetry=0.11,
        left_knee_rom_deg=52.3,
        right_knee_rom_deg=61.7,
    )

    findings = [
        GaitFinding(
            id="knee_hyperextension",
            side=Side.left,
            phase=Phase.mid_stance,
            value=11.7,
            unit="degrees",
            threshold=5.0,
            confidence=0.91,
            evidence=["Excessive knee extension during mid-stance"],
        ),
        GaitFinding(
            id="reduced_dorsiflexion_swing",
            side=Side.left,
            phase=Phase.swing,
            value=3.2,
            unit="degrees",
            threshold=5.0,
            confidence=0.88,
            evidence=["Reduced ankle dorsiflexion during swing", "Reduced estimated toe clearance"],
        ),
    ]

    engine = ClinicalKnowledgeEngine()
    findings_with_knowledge = []
    for finding in findings:
        hypothesis = engine.analyze(finding.id)
        findings_with_knowledge.append({
            "finding": asdict(finding),
            "clinical_hypothesis": asdict(hypothesis),
        })

    return {
        "metrics": asdict(metrics),
        "findings": findings_with_knowledge,
        "analysis_version": ANALYSIS_VERSION,
    }


@router.post("/{assessment_id}/run", response_model=AssessmentOut)
def run_analysis(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.video_path:
        raise HTTPException(status_code=400, detail="Upload a video before running analysis")

    assessment.status = AssessmentStatus.analyzing
    db.commit()

    # STUB: replace with real pipeline call once Phases 2-4 are built.
    results = _run_stub_analysis()

    assessment.results = results
    assessment.analysis_version = results["analysis_version"]
    assessment.knowledge_version = results["findings"][0]["clinical_hypothesis"]["knowledge_version"] if results["findings"] else None
    assessment.status = AssessmentStatus.analyzed
    db.commit()
    db.refresh(assessment)
    return assessment
