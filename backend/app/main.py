"""
App entrypoint. Wires up DB table creation (v0.1 uses create_all for
simplicity — switch to Alembic migrations before this touches real
patient data), CORS, and all routers.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import analysis, assessments, knowledge, patients, pose
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import Base, engine
from app.models import assessment, patient  # noqa: F401 — needed for create_all to see the models

configure_logging()

# Must exist before StaticFiles mounts below (it checks at import time,
# not at request time) — creating it in the startup event would be too late.
os.makedirs(settings.video_storage_path, exist_ok=True)

app = FastAPI(
    title="P&O Gait Intelligence API",
    version="0.1.0",
    description=(
        "AI-assisted gait analysis and clinical decision-support API. "
        "Does not diagnose or prescribe — surfaces measurements and "
        "possible contributors for clinician review."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # v0.1 only. Replace with Alembic migrations once the schema needs
    # to evolve without dropping data.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": app.version}


app.include_router(patients.router)
app.include_router(assessments.router)
app.include_router(analysis.router)
app.include_router(knowledge.router)
app.include_router(pose.router)

# Serves uploaded videos for playback (e.g. GET /media/{assessment_id}/{filename}).
# Starlette's StaticFiles handles Range requests, so <video> seeking works.
# Swap for a signed-URL redirect once storage moves to S3/Supabase — the
# frontend only ever sees a URL under /media, so that swap is contained here.
app.mount("/media", StaticFiles(directory=settings.video_storage_path), name="media")
