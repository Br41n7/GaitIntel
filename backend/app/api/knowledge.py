from fastapi import APIRouter

from app.clinical.knowledge_engine import ClinicalKnowledgeEngine

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/deviations/{finding_id}")
def get_knowledge_for_finding(finding_id: str):
    engine = ClinicalKnowledgeEngine()
    return engine.analyze_as_dict(finding_id)


@router.get("/deviations")
def list_known_deviations():
    engine = ClinicalKnowledgeEngine()
    return list(engine._load_all().keys())
