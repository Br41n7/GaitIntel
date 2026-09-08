# Setup

## Option A — Docker (recommended)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Backend: http://localhost:8000 (docs at /docs)
- Frontend: http://localhost:5173
- Postgres: localhost:5432 (user/pass/db: gait_user / gait_pass / gait_intelligence)

## Option B — Run locally without Docker

Backend:
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Either run Postgres locally and keep DATABASE_URL as-is,
# or point it at SQLite for quick local testing:
#   DATABASE_URL=sqlite:///./dev.db
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Verifying it works (v0.1 + Phase 2 flow)

1. Open http://localhost:5173, go to Patients, add one (e.g. identifier `PT-0001`).
2. Click into the patient, hit "New assessment."
3. Upload a walking video (`.mp4`/`.mov`/`.avi`/`.webm`) — needs to be at least
   1 second / 10 frames, or the upload is rejected with a clear error.
4. Click "Extract pose" — runs real MediaPipe pose estimation over every frame
   (this can take a few seconds depending on video length; it's synchronous
   for v0.1, see the note on background jobs below).
5. Once extraction finishes, you'll see the video with a live green skeleton
   overlay tracking hip/knee/ankle/heel/toe on both sides.
6. Click "Run gait analysis" — v0.1's analysis step is still a stub (returns
   sample metrics/findings; see `backend/app/api/analysis.py`), but it now
   runs after real pose data exists, which is where Phase 3 (joint angles,
   gait cycles, metrics) plugs in next.
7. Expand a finding to see possible contributors / assessments to consider /
   training targets, pulled live from the JSON knowledge base. Add clinician
   notes and save.

## What's real vs. stubbed right now

- **Real:** patient/assessment CRUD, video upload + validation + storage,
  video serving for playback, MediaPipe pose extraction with landmark
  smoothing and missing-landmark handling, skeleton overlay rendering, the
  knowledge engine reading JSON files, the full DB schema, the whole
  frontend flow.
- **Stubbed:** `run_analysis` still returns hardcoded metrics/findings
  instead of computing them from the now-real pose data — see the docstring
  in `backend/app/api/analysis.py`.

## Known v0.1 limitations worth knowing about

- **Root cause of the "stuck on Extracting pose" issue, fixed in this
  version:** pose extraction previously ran synchronously inside the
  HTTP request. Render's free tier gives each service 0.1 vCPU and
  512MB RAM — MediaPipe extraction that takes seconds locally can take
  minutes there, or exhaust memory and get the process killed mid-request,
  before it could even mark the assessment as failed. It now runs as a
  background task: the request returns immediately, and the frontend
  polls for status. A hard cap (`MAX_POSE_EXTRACTION_FRAMES`, default
  300 ≈ 10s at 30fps) also rejects videos too long for constrained
  hosting to process reliably — raise it via an env var once running on
  hardware that can actually handle longer clips.
- Even with the background-task fix, a **long-running extraction on the
  free tier can still be killed if the service spins down** — free web
  services spin down after 15 minutes with no incoming HTTP request,
  and that check doesn't know or care that a background task is still
  running. For anything beyond quick testing with short clips, use at
  least the Starter plan (always-on, no spin-down).
- **Schema change: if you already have a Postgres database from a
  previous deploy**, the new `error_message` column on `assessments`
  won't appear automatically — `Base.metadata.create_all()` only
  creates missing tables, not new columns on existing ones. Either
  drop and recreate the `gaitintel-db` database (fine for a testing
  environment with no real data yet) or add the column manually. This
  is exactly the class of problem Alembic migrations exist to solve —
  worth prioritizing once the schema stops changing every session.
- Pose extraction and analysis both currently accept any assessment
  regardless of video content — see `GaitAnalysisError` in
  `app/gait/pipeline.py` for the one guard that exists (rejects videos
  with fewer than 10 frames of detected pose, e.g. no human visible).
- `Base.metadata.create_all()` on startup is fine for a fresh dev DB but
  does not handle schema migrations — once real data exists, switch to
  Alembic before changing any model.

## Next up

Phase 4 (build order): the 10 deterministic gait-deviation detectors,
replacing the current empty `findings: []` with real detections computed
from the metrics Phase 3 now produces.
