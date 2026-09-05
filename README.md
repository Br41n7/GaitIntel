# P&O Gait Intelligence — MVP README

An AI-assisted gait analysis and clinical reasoning platform for Prosthetics & Orthotics students, clinicians, researchers, and gait trainers.

**This is not an autonomous diagnostic system.** It converts video into measured biomechanics, flags deviations against deterministic rules, and surfaces *possible contributors* and *things to assess* from a clinician-editable knowledge base. A human clinician interprets and decides. Nothing here diagnoses or prescribes.

```
Video → Pose → Gait Metrics → Gait Deviations → Possible Contributors → Clinical Assessments → P&O/Training Suggestions
```

---

## 1. Scope: what "MVP" actually means here

The full spec (10 phases, prosthetic/orthotic modules, knowledge editor UI, LLM explanations, versioned reports) is the *product*. It is not the MVP. Building all of it before anything is demoable means months with no working software to react to.

**v0.1 (this MVP) proves the pipeline, not the platform.**

### IN for v0.1
- Video upload → MediaPipe pose extraction → skeleton overlay
- Joint angle calculation (hip/knee/ankle), normalized to 0–100% gait cycle
- Core gait metrics (cadence, stance/swing time, step asymmetry, ROM)
- 10 deterministic deviation detectors
- A **seed** JSON knowledge base (5–10 hand-written deviation files) wired through `ClinicalKnowledgeEngine`
- Result screen: metrics, findings list, click-through to contributors/assessments/training targets
- Clinician notes + save assessment

### OUT for v0.1 (fast-follow, not abandoned)
- Trainer knowledge editor UI (edit JSON files directly for now)
- Prosthetic/orthotic modules
- LLM explanation layer
- PDF/HTML report generation
- Knowledge/model versioning enforcement
- MyoGait/ProGait/gait_analysis external adapters

The architecture (interfaces, adapter pattern) is built from day one so none of the "OUT" items require rework — they're additive, not architectural changes.

**Why this split:** everything in "IN" is required to know whether the *core idea* works — can you reliably get from video to a clinically sane finding? Everything in "OUT" is real product work, but building the editor before you've validated the pipeline risks polishing a UI on top of gait metrics that might need to change.

---

## 2. Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js + TypeScript + Tailwind + Recharts |
| Backend | Python, FastAPI |
| CV/Math | OpenCV, MediaPipe, NumPy, SciPy |
| Future ML | PyTorch / scikit-learn (not used in v0.1) |
| DB | PostgreSQL (Supabase-compatible) |
| Storage | Local filesystem, behind a storage interface (swap to S3/Supabase later) |
| Dev | Docker Compose, `.env` config |

FastAPI over Django: less ceremony for an API-first, mostly-Python-logic backend with a decoupled frontend, and the async support matters once video processing is a background job.

---

## 3. Core interfaces (build these first, literally before any UI)

```python
class PoseProvider:
    def extract(self, video_path: str) -> list[GaitFrame]: ...

class MediaPipePoseProvider(PoseProvider):
    ...

class GaitAnalyzer:
    def compute_cycles(self, frames: list[GaitFrame]) -> list[GaitCycle]: ...
    def compute_angles(self, cycles: list[GaitCycle]) -> JointAngles: ...
    def compute_metrics(self, cycles: list[GaitCycle]) -> GaitMetrics: ...

class DeviationDetector:
    def detect(self, metrics: GaitMetrics, angles: JointAngles) -> list[GaitFinding]: ...

class ClinicalKnowledgeEngine:
    def analyze(self, finding: str) -> dict:
        # returns possible_contributors, clinical_assessments, training_targets
        ...
```

### Internal data contracts

```python
GaitFrame(frame_index, timestamp, landmarks: dict)
GaitCycle(side, start_frame, end_frame, percent_normalized_frames)
JointAngles(hip, knee, ankle)  # per-frame, per-side series
GaitMetrics(cadence, stance_time, swing_time, step_asymmetry, ...)
GaitFinding(id, side, phase, value, unit, confidence)
```

**Hard rule:** the frontend never touches MediaPipe output directly. It only ever sees `GaitFrame` / `GaitMetrics` / `GaitFinding`. This is the one architectural decision that makes the later adapter swaps (MyoGait, RTMPose, whatever comes next) free instead of a rewrite.

---

## 4. Repo structure (v0.1 subset)

```
po-gait-intelligence/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── types/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/            # patients.py, assessments.py, analysis.py
│   │   ├── models/         # patient.py, assessment.py, gait.py
│   │   ├── pipeline/       # pipeline.py, result.py
│   │   ├── pose/           # base.py, mediapipe_provider.py
│   │   ├── gait/           # events.py, cycles.py, angles.py, metrics.py
│   │   ├── deviations/     # detector.py, rules.py
│   │   ├── clinical/       # knowledge_engine.py
│   │   └── storage/        # video_storage.py
│   ├── knowledge/deviations/   # seed JSON files, hand-edited for v0.1
│   ├── tests/
│   └── requirements.txt
├── docker-compose.yml
├── README.md
└── .env.example
```

Deferred until their phase: `integrations/` (external adapters), `clinical/reasoning.py` + `recommendations.py` beyond the basic engine, `models/prosthetic.py` / orthotic equivalents.

---

## 5. Build order (solo-dev realistic)

1. **Skeleton app** — FastAPI + Postgres + Next.js talking to each other. Patient CRUD, assessment CRUD, video upload endpoint. No CV yet. *Goal: prove the plumbing.*
2. **Pose pipeline** — MediaPipe extraction, landmark smoothing, skeleton overlay rendered on the uploaded video in the frontend. *Goal: prove video → pose works end-to-end.*
3. **Gait math** — angle calculation, gait event/cycle segmentation, 0–100% normalization, metrics computation. *Goal: numbers you'd trust enough to show a clinician.*
4. **Deviation detectors** — implement the 10 rules against real metrics output. *Goal: findings with confidence scores, not fake AI.*
5. **Knowledge engine + seed knowledge base** — 5–10 JSON files, engine wired to return contributors/assessments/training targets per finding.
6. **Result screen** — metrics summary, findings list, click-through detail, clinician notes, save.

Stop here. That's v0.1. Ship it, use it on real videos, see where the gait math or the deviation thresholds are wrong before building the editor UI on top of them.

**Fast-follow (v0.2+, in this order):** trainer knowledge editor → versioning → prosthetic/orthotic modules → LLM explanation layer → PDF reports → external adapters (MyoGait/ProGait) → advanced ML (Phase 10).

---

## 6. v0.1 acceptance test

A user can:
1. Create a patient and an assessment
2. Upload a walking video
3. Run analysis and see the pose skeleton overlaid
4. See hip/knee/ankle angle trajectories over the gait cycle
5. See basic gait metrics (cadence, stance/swing time, asymmetry, ROM)
6. See at least several of the 10 deviations detected with confidence scores
7. Click a finding and see possible contributors, assessments to consider, and training targets pulled from the seed knowledge base
8. Add clinician notes and save the assessment

No PDF report, no editor, no prosthetic module, no LLM — those are v0.2.

---

## 7. Non-negotiables carried through every phase

- Never call a finding a diagnosis. Vocabulary is always: *possible contributor*, *consider assessing*, *pattern may be consistent with*, *requires clinical correlation*.
- Confidence is always separated: detection confidence ≠ interpretation confidence ≠ evidence strength. Never a single "AI confidence" number.
- Any future report/output includes: *"This system provides research/clinical decision-support information and does not independently diagnose conditions or prescribe treatment. Findings require assessment and interpretation by an appropriately qualified clinician."*
# GaitIntel
