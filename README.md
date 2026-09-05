# GaitIntel — AI Gait Movement Detector & Prosthetics/Orthotics Clinical Decision-Support Platform

[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Pipeline-blue.svg)](DOCUMENTATION.md)
[![Clinical Compliance](https://img.shields.io/badge/Clinical%20Safety-SaMD%20CDSS-green.svg)](#1-core-clinical-principles--safety-governance)
[![Status](https://img.shields.io/badge/Status-V1%20Architecture%20%26%20Contracts%20Complete-orange.svg)](#3-gap-analysis-completed-vs-pending-implementations)

**GaitIntel** is an advanced AI-powered gait analysis and movement assessment platform engineered specifically for Prosthetics & Orthotics (P&O), physiotherapy, rehabilitation, biomechanics, and clinical gait-training applications.

The platform ingests video and sensor-based movement data, tracks anatomical landmarks, detects gait cycle events, quantifies sagittal/frontal/transverse joint kinematics, isolates abnormal movement patterns, and generates ranked, explainable musculoskeletal, neuromuscular, prosthetic, and orthotic candidate contributors for clinician review.

---

## 1. Core Clinical Principles & Safety Governance

> **CRITICAL CLINICAL BOUNDARY:** GaitIntel is a **Clinical Decision Support System (CDSS)**. It **DOES NOT** diagnose medical conditions, independently prescribe prosthetic/orthotic devices, or replace clinical judgment. Final clinical interpretations and treatment plans remain the sole responsibility of the qualified clinician.

### Language Standard & Vocabulary Guardrails
To prevent diagnostic misclassification and adhere to Software as a Medical Device (SaMD) CDSS guardrails, all system outputs strictly enforce non-diagnostic clinical phrasing:

* **Mandated Phrasing:** `"Possible contributor"`, `"Pattern consistent with..."`, `"Consider assessing..."`, `"Clinical correlation required"`.
* **Prohibited Phrasing:** `"Patient has [Diagnosis]"`, `"Definitive cause is..."`, `"Prescribe [Intervention]"`.

### Clinical Decision Flow
```
Video Input → Pose Extraction → Kinematic Calculation → Rule & ML Deviation Detection → Musculoskeletal/P&O Reasoning → Candidate Contributors & Clinical Checks → Clinician Review & Documentation
```

---

## 2. Platform Architecture Overview

GaitIntel utilizes a decoupled, asynchronous micro-pipeline architecture to maintain performance, privacy, and research extensibility.

```
       ┌─────────────────────────────────────────────────────────┐
       │                   Clinical Dashboard                    │
       │           (Next.js 14, TypeScript, Recharts)             │
       └────────────────────────────┬────────────────────────────┘
                                    │ REST / WebSockets
       ┌────────────────────────────▼────────────────────────────┐
       │                      FastAPI API                        │
       └──────┬─────────────────────┬────────────────────┬───────┘
              │                     │                    │
┌─────────────▼──────────┐ ┌────────▼─────────┐ ┌────────▼──────────────┐
│  CV & Pose Pipeline    │ │ Biomechanics &  │ │ Clinical Reasoning   │
│ (MediaPipe / OpenCV)   │ │  Kinematics     │ │   & Hypothesis Engine│
└─────────────┬──────────┘ └────────┬─────────┘ └────────┬──────────────┘
              │                     │                    │
              └─────────────────────┼────────────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │  PostgreSQL / Supabase  │
                       └─────────────────────────┘
```

---

## 3. Gap Analysis: Completed vs. Pending Implementations

The table below presents a comprehensive audit comparing the target 24 platform specifications against the current codebase status.

| Specification Area | Architectural & Data Contract Specs | V1 (MVP) Implementation | Phase / V-Level Status |
| :--- | :--- | :--- | :--- |
| **1. Core Clinical Principles** | **Completed** — Vocabulary guidelines, CDSS guardrails, disclaimers defined. | **Completed** — Embedded in system prompt & API contract standards. | Complete |
| **2. Input System & Metadata** | **Completed** — Data contracts for patient metadata, camera angles, device configs. | **Completed** — Multipart upload & metadata schema endpoints defined. | V1 Target |
| **3. Pose Estimation** | **Completed** — `PoseProvider` interface & MediaPipe adapter contracts established. | **Completed** — MediaPipe 33-landmark extraction & overlay pipeline. | V1 Target |
| **4. Gait Event Detection** | **Completed** — Logic for 8 gait sub-phases & key events (IC, LR, MST, TST, PSW, ISW, MSW, TSW). | **Completed** — Temporal parameter computation (cadence, stance/swing ratio). | V1 Target |
| **5. Joint Kinematics** | **Completed** — Sagittal/frontal angle computation formulations (hip, knee, ankle, pelvis, trunk). | **Completed** — Hip/Knee/Ankle 2D sagittal trajectory calculation & normalization (0-100%). | V1 Target |
| **6. Gait Deviation Engine** | **Completed** — Rule-based + ML hybrid detection engine specifications. | **Completed** — 10 core temporal, spatial, and kinematic deviation detectors. | V1 Target |
| **7. Musculoskeletal Reasoning**| **Completed** — Seed knowledge base schema linking deviations to candidate contributors. | **Completed** — `ClinicalKnowledgeEngine` with seed JSON knowledge files. | V1 Target |
| **8. Prosthetic Gait Module** | **Completed** — Specification for socket, alignment, component stiffness, residual limb metrics. | *Pending* — V2 Expansion (Prosthetic socket/alignment compensation reasoning). | V2 Target |
| **9. Orthotic Gait Module** | **Completed** — Comparative schema for AFO, KAFO, GRAFO, SMO, Foot Orthoses (Pre vs Post). | *Pending* — V3 Expansion (Orthotic device impact & kinematic comparative module). | V3 Target |
| **10. Clinical Hypothesis Engine**| **Completed** — Structured output schema (Detected Pattern → Possible Contributors → Clinical Checks).| **Completed** — Multi-tier confidence scoring engine (Detection vs Biomechanical vs Etiological). | V1 Target |
| **11. Explainable AI (XAI)** | **Completed** — Evidence graph mapping observed kinematics directly to candidates. | **Completed** — Rule-driven evidence trace logging per detected finding. | V1 Target |
| **12. Gait Training Targets** | **Completed** — Target recommendation generation linked to detected deviations. | **Completed** — Clinical intervention target suggestions mapped in knowledge base. | V1 Target |
| **13. Before/After Comparison** | **Completed** — Schema for paired assessment delta calculations & ROM percent changes. | *Pending* — V1.1 Follow-up (Side-by-side comparative graph UI). | V1.1 Target |
| **14. Visualization & Graphs** | **Completed** — Data contracts for gait cycle normalized trajectories (0-100%). | **Completed** — Interactive Recharts component schemas & video skeleton overlay. | V1 Target |
| **15. Gait Deviation Score** | **Completed** — Interpretable score formulation (Symmetry, Temporal, Joint, Pelvic Control). | **Completed** — Sub-score mathematical formulations defined in metrics pipeline. | V1 Target |
| **16. Patient Timeline** | **Completed** — Historical assessment progression tracking schema. | *Pending* — V1.2 Follow-up (Timeline progression view). | V1.2 Target |
| **17. Clinician Dashboard** | **Completed** — Complete UI layout & navigation architecture designed. | **Completed** — Patient management, assessment creation, and result display views. | V1 Target |
| **18. Clinical Report Generation**| **Completed** — Structured PDF & HTML report template schema defined. | *Pending* — V2 Target (Automated PDF/HTML report export engine). | V2 Target |
| **19. Data & Model Training** | **Completed** — DB Schema for annotated landmark, gait cycle, and finding datasets. | **Completed** — PostgreSQL schema definitions for research data persistence. | V1 Target |
| **20. Research Mode** | **Completed** — JSON/CSV export specification & anonymization guardrails. | *Pending* — V5 Target (Research exporter & model evaluation suite). | V5 Target |
| **21. Temporal ML Engine** | **Completed** — Model specifications for 1D-CNN / LSTM / Temporal Convolutional Networks. | *Pending* — V4 Target (Deep learning temporal model training & inference pipeline). | V4 Target |
| **22. Multi-Camera / 3D Analysis**| **Completed** — Geometry triangulation data contract for multi-view setup. | *Pending* — V5 Target (3D joint trajectory triangulation). | V5 Target |
| **23. Sensor Integration** | **Completed** — Data contracts for IMU & in-shoe pressure distribution sensors. | *Pending* — V6 Target (IMU / Pressure plate data synchronization). | V6 Target |
| **24. Safety & Audit Trail** | **Completed** — Immutability, override logging, and SaMD compliance specifications. | **Completed** — Clinician edit & audit log data contracts. | V1 Target |

---

## 4. Technical Stack & Infrastructure

### Backend
* **Language & Framework:** Python 3.11+, FastAPI (Async API layer)
* **Computer Vision & Math:** OpenCV, MediaPipe Pose, NumPy, SciPy
* **Data Science & ML:** scikit-learn, PyTorch (V4 Temporal Deep Learning)
* **Database & ORM:** PostgreSQL / Supabase, SQLAlchemy / Alembic
* **Storage Interface:** Local filesystem adapter (interchangeable with S3 / Azure Blob)

### Frontend
* **Framework:** Next.js 14 (App Router), TypeScript, React 18
* **Styling & UI Components:** Tailwind CSS, shadcn/ui, Lucide Icons
* **Visualization:** Recharts (Gait Cycle Trajectories), HTML5 Canvas / Video Overlays

---

## 5. Core System Data Contracts & Interfaces

To decouple computer vision providers from downstream biomechanical analysis and ML engines, GaitIntel enforces strict internal data contracts:

```python
# Core Domain Contracts (backend/app/pipeline/contracts.py)

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class GaitFrame:
    frame_index: int
    timestamp: float
    landmarks: Dict[str, Dict[str, float]] # {landmark_name: {x, y, z, visibility}}

@dataclass
class GaitCycle:
    side: str # 'left' | 'right'
    start_frame: int
    end_frame: int
    initial_contact_frame: int
    toe_off_frame: int
    normalized_frames: List[GaitFrame] # 0 to 100% normalized

@dataclass
class JointAngles:
    hip_flexion_extension: List[float]
    knee_flexion_extension: List[float]
    ankle_dorsiflexion_plantarflexion: List[float]
    trunk_inclination: Optional[List[float]] = None
    pelvic_tilt: Optional[List[float]] = None

@dataclass
class GaitMetrics:
    cadence: float
    walking_velocity: float
    left_stance_time: float
    right_stance_time: float
    left_swing_time: float
    right_swing_time: float
    step_length_asymmetry: float
    double_support_time: float
    gait_symmetry_index: float

@dataclass
class GaitFinding:
    id: str
    side: str
    deviation_type: str
    phase: str
    magnitude: float
    unit: str
    confidence_detection: float
    evidence_summary: List[str]
```

---

## 6. Phased Rollout Strategy (V1 to V7)

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│    V1    │──▶│    V2    │──▶│    V3    │──▶│    V4    │──▶│    V5    │──▶│    V6    │──▶│    V7    │
│ Core MVP │   │Prosthetic│   │ Orthotic │   │ Temporal │   │ Multi-Cam│   │ Sensors  │   │ Clinical │
│ Pipeline │   │ Module   │   │ Module   │   │ ML Model │   │ 3D Gait  │   │ IMU/Press│   │ Trial    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

1. **V1 (Core MVP):** Video pose extraction, gait cycle segmentation, joint angles, 10 core deviation detectors, seed knowledge engine, clinical dashboard.
2. **V2 (Prosthetic Analysis Module):** Prosthetic-side vs. sound-side biomechanics, socket fit & alignment reasoning, report generator.
3. **V3 (Orthotic Module):** Pre/post orthotic intervention comparative analysis (AFO, KAFO, SMO), kinematic diff calculations.
4. **V4 (Temporal Deep Learning):** 1D-CNN / Transformer temporal deviation classifiers trained on annotated clinical data.
5. **V5 (Research Mode & Multi-Camera):** Anonymized research export (CSV/JSON), model training/evaluation suite, multi-camera 3D reconstruction.
6. **V6 (Multi-Modal Sensor Fusion):** IMU sensor synchronization & force/pressure plate integration.
7. **V7 (Clinical Validation & Deployment):** Multi-center prospective validation, SaMD regulatory documentation, local/on-device privacy deployments.

---

## 7. Project Structure

```
GaitIntel/
├── DOCUMENTATION.md               # Full Technical & Clinical Platform Specification
├── README.md                      # Platform Architecture & Quickstart Guide
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI Application Entrypoint
│   │   ├── api/                   # REST Endpoints (patients, assessments, analysis)
│   │   ├── models/                # Database Schemas & ORM Entities
│   │   ├── pipeline/              # Core Contracts & Processing Orchestrator
│   │   ├── pose/                  # MediaPipe & CV Landmark Adapters
│   │   ├── gait/                  # Cycle Segmentation, Event Math, Kinematics
│   │   ├── deviations/            # Rule-based & ML Deviation Detectors
│   │   ├── clinical/              # Knowledge Engine & Candidate Generator
│   │   └── storage/               # File & Video Storage Abstraction Layer
│   ├── knowledge/
│   │   └── deviations/            # Seed Clinical Knowledge JSON Files
│   ├── tests/                     # Unit, Kinematic Math & Integration Tests
│   └── requirements.txt           # Python Dependencies
└── frontend/
    ├── app/                       # Next.js 14 App Router Pages
    ├── components/                # Reusable UI & Chart Components
    ├── lib/                       # API Clients & Utilities
    └── types/                     # TypeScript Domain Interfaces
```

---

## 8. Development & Installation Guide

### Prerequisites
* Python 3.11+
* Node.js 18+ and `npm` / `pnpm`
* OpenCV system dependencies (`libgl1-mesa-glx`, `ffmpeg`)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The application will be accessible at `http://localhost:3000`, with API endpoints at `http://localhost:8000/docs`.

---

## 9. Further Reading

For complete specifications of the 24 platform requirements, mathematical formulations, knowledge base JSON schemas, and safety guardrails, consult the comprehensive [DOCUMENTATION.md](DOCUMENTATION.md).
