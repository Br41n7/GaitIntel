# GaitIntel — AI-Assisted Gait Analysis & Clinical Decision-Support Platform

An AI-assisted gait analysis and clinical reasoning platform for Prosthetics & Orthotics students, clinicians, researchers, and gait trainers.

**This is not an autonomous diagnostic system.** It converts video into measured biomechanics, flags deviations against deterministic rules, and surfaces *possible contributors* and *things to assess* from a clinician-editable knowledge base. A human clinician interprets and decides. Nothing here diagnoses or prescribes.

```
Video → Pose → Gait Metrics → Gait Deviations → Possible Contributors → Clinical Assessments → P&O/Training Suggestions
```

For the full target architecture (all 24 planned subsystems, V1–V7 roadmap), see **[DOCUMENTATION.md](DOCUMENTATION.md)** — that document describes where this is headed, not what's running today. This README describes what's actually built and working right now.

---

## 1. Current Implementation Status

Status as of the latest commit. "Built" means real, tested code — not a data model that exists for it, not a route that returns a placeholder.

| Area | Status | Notes |
|---|---|---|
| Patient / assessment CRUD | ✅ Built | Full DB-backed CRUD, tested end to end |
| Video upload, validation, storage | ✅ Built | Rejects too-short/corrupt uploads; local filesystem storage behind a swappable interface |
| Pose extraction (MediaPipe) | ✅ Built | Real inference — hip/knee/ankle/heel/toe landmarks, both sides, per frame |
| Landmark smoothing / missing-landmark handling | ✅ Built | Exponential smoothing + hold-last-good-value below visibility threshold |
| Skeleton overlay on video | ✅ Built | Canvas overlay synced to video playback by timestamp |
| Clinical knowledge engine | ✅ Built | Loads JSON deviation files, returns possible contributors / assessments / training targets |
| Joint-angle calculation | ✅ Built | `calculate_angle()` + per-frame hip/knee/ankle flexion series, validated against synthetic ground truth |
| Gait-cycle segmentation | ✅ Built | Initial-contact/toe-off detection (kinematic method, no force plate) + 0-100% cycle normalization |
| Real gait metrics (cadence, stance/swing time, ROM, asymmetry) | ✅ Built | Computed from real pose data — see caveats in `backend/app/gait/metrics.py` (`walking_velocity_m_s` is intentionally always `None` — no camera calibration exists to convert normalized coordinates to real-world units) |
| Deviation detectors (the 10 rules) | ❌ Not built | Phase 4 — `findings: []` with an explicit `findings_status` message rather than fake data |
| Confidence separation (detection / interpretation / evidence) | 🟡 Partial | Data model supports it; not populated until Phase 4 findings exist |
| Trainer knowledge-editor UI | ❌ Not built | v0.2+ |
| Prosthetic / orthotic modules | ❌ Not built | v0.2+ (documented as V2/V3 in the vision doc) |
| PDF/HTML report generation | ❌ Not built | v0.2+ |
| Database migrations (Alembic) | ❌ Not wired up | Listed in `requirements.txt` but unused — schema currently created via `Base.metadata.create_all()`, dev-only |
| ML-based classifiers, multi-camera 3D, sensor fusion, audit ledger, research export | ❌ Not built | These are V4–V7 in the vision doc, not started |

If you're deciding what to work on next, anything marked ❌ above is real, uncommitted work — not polish on something that already works.

---

## 2. Core Clinical Principles & Vocabulary Guardrails

> **Clinical boundary:** GaitIntel is a decision-support tool, not a diagnostic one. It does not diagnose medical conditions, independently prescribe devices, or replace clinical judgment.

* **Use:** "possible contributor," "pattern may be consistent with," "consider assessing," "requires clinical correlation."
* **Never:** "patient has [diagnosis]," "definitive cause is...," "prescribe [intervention]."

Confidence is always reported at the level it was actually computed — detection confidence is not the same claim as an interpretation confidence, and neither is a diagnosis. Don't let output language imply more certainty than a given layer of the pipeline actually has.

---

## 3. Technology Stack (as actually used)

**Backend:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, OpenCV, MediaPipe, NumPy, SciPy.

**Frontend:** React + Vite, TypeScript, Tailwind CSS, Recharts. *(Not Next.js — Vite was chosen deliberately to avoid learning a new backend and a new frontend framework simultaneously; see project history for the reasoning.)*

**Storage:** Local filesystem behind a `StorageBackend` interface, designed to swap for S3/Supabase Storage later without touching calling code.

**Deployment:** Docker Compose for local dev; Render Blueprint (`render.yaml`) for hosted testing — see `DEPLOY.md`.

---

## 4. Project Structure (as it actually exists)

```
GaitIntel/
├── DOCUMENTATION.md          # Full target-state specification (V1–V7 vision, not current status)
├── README.md                 # This file — what's actually built
├── DEPLOY.md                 # Render deployment instructions
├── render.yaml                # Render Blueprint
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/               # patients, assessments, pose, analysis (stub), knowledge
│   │   ├── models/             # SQLAlchemy: Patient, Assessment
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── pipeline/           # gait_types.py (internal data contracts), video_validation.py
│   │   ├── pose/                # PoseProvider interface, MediaPipe implementation, smoothing
│   │   ├── clinical/            # ClinicalKnowledgeEngine
│   │   └── storage/             # StorageBackend interface, local implementation
│   ├── knowledge/deviations/   # Seed clinical knowledge JSON files
│   ├── tests/
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/               # Dashboard, Patients, PatientDetail, AssessmentDetail
        ├── components/          # Layout, VideoUpload, PoseOverlayVideo, FindingCard
        ├── lib/api.ts
        └── types/
```

Note: `app/gait/` and `app/deviations/` (referenced as planned locations in DOCUMENTATION.md for Phase 3/4 code) don't exist yet — they'll be created when that work starts.

---

## 5. Development Setup

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
API runs at `http://localhost:8000` (docs at `/docs`).

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173` (Vite's default — not 3000).

### Docker (both + Postgres)
```bash
cp backend/.env.example backend/.env
docker compose up --build
```

See `DEPLOY.md` for deploying a test instance to Render.

---

## 6. Verifying the current build works

1. Add a patient, create an assessment.
2. Upload a walking video (`.mp4`/`.mov`/`.avi`/`.webm`, ≥1s / ≥10 frames).
3. Click "Extract pose" — runs real MediaPipe inference; you'll see a live skeleton overlay once done.
4. Click "Run gait analysis" — returns the current stub metrics/findings (real computation is Phase 3, not built yet).
5. Expand a finding, add clinician notes, save.

---

## 7. What's next (Phase 4)

The 10 deterministic gait-deviation detectors, computed from the real metrics and joint-angle trajectories Phase 3 now produces (knee hyperextension, excessive/reduced knee flexion, reduced dorsiflexion, circumduction, hip hiking, trunk lean, step/stance-time asymmetry, etc.) — replacing the current `findings: []` placeholder in `backend/app/api/analysis.py`. Each detector's output routes through the existing `ClinicalKnowledgeEngine`, which is already built and tested.

For the long-term roadmap beyond that (prosthetic/orthotic modules, ML classifiers, multi-camera 3D, sensor fusion, clinical validation), see `DOCUMENTATION.md` — treat every section there as a target to build toward, not a status report.
