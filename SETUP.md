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

- Pose extraction runs synchronously in the request — fine for short clinic
  clips, but a multi-minute video will hold the HTTP connection open for a
  while. Move this to a background task (FastAPI `BackgroundTasks`, or a
  proper queue like Celery/RQ) before this goes anywhere near production
  video lengths.
- `Base.metadata.create_all()` on startup is fine for a fresh dev DB but
  does not handle schema migrations — once real data exists, switch to
  Alembic before changing any model.

## Next up

Phase 3 (build order): joint-angle calculation, gait-cycle segmentation,
gait metrics — replacing the `_run_stub_analysis()` function with real
computation over `assessment.pose_data`.
