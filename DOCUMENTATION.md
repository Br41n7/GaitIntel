# GaitIntel — Clinical Decision Support & Biomechanical Analytics Specification

**Version:** 1.0.0
**Classification:** Software as a Medical Device (SaMD) — Clinical Decision Support System (CDSS)
**Target Audience:** Prosthetists, Orthotists, Biomechanists, Physiotherapists, Clinical Software Engineers

---

## Table of Contents
1. [Core Clinical Principles & Safety Boundaries](#1-core-clinical-principles--safety-boundaries)
2. [Input System & Multi-Modal Data Collection](#2-input-system--multi-modal-data-collection)
3. [Pose Estimation & Landmark Tracking](#3-pose-estimation--landmark-tracking)
4. [Gait Event Detection & Spatiotemporal Parameter Math](#4-gait-event-detection--spatiotemporal-parameter-math)
5. [Joint Kinematics & Angular Trajectories](#5-joint-kinematics--angular-trajectories)
6. [Gait-Deviation Detection Engine](#6-gait-deviation-detection-engine)
7. [Musculoskeletal & Neuromuscular Reasoning Engine](#7-musculoskeletal--neuromuscular-reasoning-engine)
8. [Prosthetic Gait Analysis Module](#8-prosthetic-gait-analysis-module)
9. [Orthotic Gait Analysis Module](#9-orthotic-gait-analysis-module)
10. [Clinical Hypothesis & Reasoning Engine](#10-clinical-hypothesis--reasoning-engine)
11. [AI Architecture & Modular Pipeline](#11-ai-architecture--modular-pipeline)
12. [Explainable AI (XAI) & Evidence Lineage](#12-explainable-ai-xai--evidence-lineage)
13. [Gait Training Target Generator](#13-gait-training-target-generator)
14. [Comparative Analytics (Before/After & Intervention Tracking)](#14-comparative-analytics-beforeafter--intervention-tracking)
15. [Visualization & Interactive Kinematic Dashboard](#15-visualization--interactive-kinematic-dashboard)
16. [Composite Gait Deviation Scoring Framework](#16-composite-gait-deviation-scoring-framework)
17. [Longitudinal Patient Timeline](#17-longitudinal-patient-timeline)
18. [Clinician Dashboard Workflow](#18-clinician-dashboard-workflow)
19. [Automated Clinical Report Engine](#19-automated-clinical-report-engine)
20. [Data Architecture & Model Fine-Tuning Persistence](#20-data-architecture--model-fine-tuning-persistence)
21. [Research Mode & Analytics Export Engine](#21-research-mode--analytics-export-engine)
22. [Technology Stack & System Integration](#22-technology-stack--system-integration)
23. [MVP Development Strategy (V1 to V7 Roadmap)](#23-mvp-development-strategy-v1-to-v7-roadmap)
24. [Clinical Safety, Auditability & Validation Protocols](#24-clinical-safety-auditability--validation-protocols)

---

## 1. Core Clinical Principles & Safety Boundaries

GaitIntel is strictly engineered as a **Clinical Decision Support System (CDSS)**. It transforms unorganized video or sensor streams into objective biomechanical measures, compares those measures against deterministic thresholds and learned distributions, and surfaces *candidate explanatory factors* alongside *recommended physical examinations*.

### Non-Diagnostic Mandate
Under no circumstances does GaitIntel generate autonomous diagnoses, disease labels, or binding prosthetic/orthotic prescriptions.

```
+-------------------------------------------------------------------------------+
|                               CLINICAL BOUNDARY                               |
|                                                                               |
|  AUTOMATED MEASUREMENT   --->   DETERMINISTIC & ML DETECTORS   --->   REASONING |
|  [Objective Kinematics]         [Abnormal Pattern Detection]         [Candidates] |
|                                                                               |
|                                         │                                     |
|                                         ▼                                     |
|                              HUMAN CLINICIAN REVIEW                           |
|                       [Manual Muscle Test / ROM / Final Decision]             |
+-------------------------------------------------------------------------------+
```

### Vocabulary Guardrails
System prompts, user interfaces, JSON outputs, and PDF reports strictly enforce standardized clinical decision-support nomenclature:
* **Allowed Terms:** `"Possible contributor"`, `"Pattern consistent with..."`, `"Consider assessing..."`, `"Clinical correlation required"`, `"Observed kinematic deviation"`.
* **Prohibited Terms:** `"Patient suffers from..."`, `"Diagnosed with..."`, `"Definitive etiology"`, `"Prescribed treatment"`.

---

## 2. Input System & Multi-Modal Data Collection

GaitIntel ingests multi-plane video data alongside clinical metadata to establish a standardized baseline.

### Video Acquisition Modalities
* **Sagittal Plane:** Left and right lateral views for hip/knee/ankle flexion-extension and step length.
* **Frontal Plane:** Anterior and posterior views for pelvic drop, trunk lean, hip abduction/adduction, and base-of-support width.
* **Functional Movements:** Walking at comfortable/fast speeds, standing balance, sit-to-stand transitions, ramp negotiation, and stair climbing.

### Clinical Metadata Schema
```json
{
  "patient_id": "P-98402",
  "age": 48,
  "sex": "female",
  "height_cm": 168.0,
  "weight_kg": 65.5,
  "affected_limb": "left",
  "device_category": "prosthetic",
  "device_configuration": {
    "socket_type": "Suction Suspension Transfemoral",
    "knee_joint": "Polycentric Hydraulic",
    "foot_type": "Carbon Energy Storage & Return (ESAR)"
  },
  "walking_speed_category": "self_selected_comfortable",
  "walking_surface": "level_firm",
  "assistance_level": "independent_no_canes",
  "primary_clinical_condition": "Transfemoral Amputation (etiology: trauma)",
  "assessment_date": "2026-09-05T14:30:00Z"
}
```

---

## 3. Pose Estimation & Landmark Tracking

GaitIntel leverages MediaPipe Pose (33 3D landmarks) as its primary V1 pose provider, abstracted behind a generic `PoseProvider` Python interface to enable seamless hot-swapping with OpenPose, YOLO-Pose, or RTMPose.

### Key Anatomical Landmarks Tracked
* **Trunk / Axial:** Ear, Shoulder ($p_{11}, p_{12}$), Trunk Center, Pelvis / Mid-Hip ($p_{23}, p_{24}$).
* **Lower Limb (Bilateral):**
  * Hip Joint Center ($p_{23}, p_{24}$)
  * Knee Joint Center ($p_{25}, p_{26}$)
  * Ankle Joint Center ($p_{27}, p_{28}$)
  * Heel Landmark ($p_{29}, p_{30}$)
  * Toe / Forefoot Landmark ($p_{31}, p_{32}$)

### Prosthetic & Orthotic Landmark Adaptation
For prosthetic users, standard keypoint detectors often experience landmark drift due to socket geometry or non-human reflectivity. GaitIntel provides:
1. **Manual Landmark Adjustment:** Interactive UI canvas allowing clinicians to drag keypoints (e.g., prosthetic knee pivot, socket brim, prosthetic ankle bolt).
2. **Keypoint Confidence Filtering:** Automatic interpolation for frames where landmark visibility falls below $\tau_{vis} = 0.65$.

---

## 4. Gait Event Detection & Spatiotemporal Parameter Math

### Gait Cycle Sub-Phases
GaitIntel automatically segments continuous walking sequences into discrete gait cycles ($0\%$ to $100\%$) and detects 8 sub-phases:

```
[──── Stance Phase (~60%) ────] [──── Swing Phase (~40%) ────]
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│  IC  │  LR  │ MST  │ TST  │ PSW  │ ISW  │ MSW  │ TSW  │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
  0%    12%    31%    50%    62%    75%    87%   100%
```

1. **Initial Contact (IC):** $0\%$ gait cycle. Detected via local minimum of vertical heel landmark velocity $v_y^{\text{heel}} \approx 0$ and heel elevation.
2. **Loading Response (LR):** $0\% - 12\%$. Heel strike to forefoot contact.
3. **Mid-Stance (MST):** $12\% - 31\%$. Contralateral toe-off to body weight vector over stance foot.
4. **Terminal Stance (TST):** $31\% - 50\%$. Heel rise to contralateral initial contact.
5. **Pre-Swing (PSW):** $50\% - 62\%$. Contralateral IC to ipsilateral toe-off.
6. **Initial Swing (ISW):** $62\% - 75\%$. Toe-off to maximum knee flexion.
7. **Mid-Swing (MSW):** $75\% - 87\%$. Maximum knee flexion to vertical tibia alignment.
8. **Terminal Swing (TSW):** $87\% - 100\%$. Vertical tibia to next Initial Contact.

### Spatiotemporal Formulas
* **Cadence ($C$):**
  $$C = \frac{\text{Steps}}{\text{Duration (min)}} = \frac{N_{\text{steps}}}{\Delta t} \times 60$$
* **Stance / Swing Duration Ratio:**
  $$\text{Stance \%} = \left(\frac{t_{\text{toe\_off}} - t_{\text{initial\_contact}}}{t_{\text{next\_ic}} - t_{\text{initial\_contact}}}\right) \times 100$$
* **Step Length Asymmetry Ratio (ASI):**
  $$\text{ASI} = \left( \frac{\text{Step Length}_{\text{left}} - \text{Step Length}_{\text{right}}}{\frac{1}{2}\left(\text{Step Length}_{\text{left}} + \text{Step Length}_{\text{right}}\right)} \right) \times 100$$

---

## 5. Joint Kinematics & Angular Trajectories

Joint angles are computed per frame using vector algebra across 2D/3D landmark coordinates.

### Angle Calculation Formulas
For three joint landmarks $A$ (proximal), $B$ (vertex joint center), and $C$ (distal):

$$\vec{u} = \vec{A} - \vec{B}, \quad \vec{v} = \vec{C} - \vec{B}$$

$$\theta = \arccos\left( \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|} \right) \times \frac{180}{\pi}$$

```
    A (Hip)
     \
      \  u
       \
        B (Knee) ──θ (Knee Flexion Angle)
       /
      /  v
     /
    C (Ankle)
```

### Tracked Kinematic Degrees of Freedom
* **Hip:** Flexion (+) / Extension (-), Abduction / Adduction (frontal).
* **Knee:** Flexion (+) / Extension (0°) / Hyperextension (-).
* **Ankle:** Dorsiflexion (+) / Plantarflexion (-).
* **Pelvis:** Anterior / Posterior Tilt (sagittal), Contralateral Drop / Obliquity (frontal).
* **Trunk:** Forward inclination (sagittal), Lateral lean (frontal).

---

## 6. Gait-Deviation Detection Engine

GaitIntel uses a deterministic rule-based evaluator combined with trained classifier models to flag abnormalities.

### Core Rule Matrix (Sample of 10 Evaluators)

| Deviation ID | Abnormality Name | Phase Affected | Kinematic / Spatial Trigger Threshold |
| :--- | :--- | :--- | :--- |
| `DEV-01` | **Excessive Knee Recurvatum** | Mid-Stance ($12-31\%$) | Knee Angle $< -5^{\circ}$ (hyperextension) |
| `DEV-02` | **Reduced Swing Dorsiflexion** | Mid-Swing ($75-87\%$) | Ankle Dorsiflexion $< 0^{\circ}$ (plantarflexed) |
| `DEV-03` | **Trendelenburg / Pelvic Drop** | Mid-Stance ($12-31\%$) | Contralateral Pelvic Drop $> 5^{\circ}$ |
| `DEV-04` | **Ipsilateral Lateral Trunk Lean**| Stance Phase ($0-60\%$) | Lateral Trunk Lean $> 8^{\circ}$ toward stance side |
| `DEV-05` | **Vaulting** | Contralateral Swing | Ipsilateral Ankle Plantarflexion $> 15^{\circ}$ during mid-stance |
| `DEV-06` | **Circumduction** | Swing Phase ($62-100\%$) | Ankle Lateral Displacement $> 2.5 \times$ baseline width |
| `DEV-07` | **Inadequate Knee Swing Flexion**| Initial Swing ($62-75\%$) | Peak Knee Flexion $< 45^{\circ}$ (Normal $\approx 60-65^{\circ}$) |
| `DEV-08` | **Foot Slap** | Loading Response ($0-12\%$) | Ankle Plantarflexion Angular Velocity $> 300^{\circ}/\text{sec}$ |
| `DEV-09` | **Step Length Asymmetry** | Double Support | $\| \text{ASI} \| > 15\%$ difference between limbs |
| `DEV-10` | **Anterior Pelvic Tilt** | Entire Cycle ($0-100\%$) | Anterior Pelvic Angle $> 15^{\circ}$ average |

---

## 7. Musculoskeletal & Neuromuscular Reasoning Engine

Once a deviation is identified, the `ClinicalKnowledgeEngine` queries a knowledge base mapping biomechanical symptoms to potential clinical drivers.

```
                  ┌─────────────────────────────────┐
                  │ Detected Gait Deviation         │
                  │ e.g., Knee Hyperextension (MST) │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ Knowledge Engine Lookup         │
                  │ (rules + causal graph)          │
                  └────────────────┬────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Muscle Weakness │       │ Range of Motion │       │ Device / Align  │
│  · Quadriceps   │       │  · Gastrocnemius│       │  · Excessive    │
│  · Plantarflex  │       │    contracture  │       │    plantarflex  │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ Recommended Clinical Checks     │
                  │  · MMT Quadriceps (L3-L4)       │
                  │  · Passive Ankle ROM Test       │
                  │  · Inspect AFO / Socket align   │
                  └─────────────────────────────────┘
```

---

## 8. Prosthetic Gait Analysis Module

Dedicated specifically to transfemoral, transtibial, and upper-level lower-limb amputees.

### Specialized Prosthetic Deviations & Candidates

```
  OBSERVED GAIT DEVIATION            POSSIBLE PROSTHETIC CONTRIBUTOR           RECOMMENDED CLINICAL CHECK
┌───────────────────────────┐      ┌───────────────────────────────────┐     ┌────────────────────────────┐
│ Vaulting / Hip Hiking     │ ───► │ · Prosthetic length too long      │ ──► │ · Check limb length sync   │
│ (Sound side stance)       │      │ · Inadequate knee flex resistance │     │ · Verify suspension vacuum │
└───────────────────────────┘      └───────────────────────────────────┘     └────────────────────────────┘
┌───────────────────────────┐      ┌───────────────────────────────────┐     ┌────────────────────────────┐
│ Excessive Trunk Lean      │ ───► │ · Weak socket lateral wall support│ ──► │ · Inspect socket adduction │
│ (Prosthetic side stance)  │      │ · Prosthetic foot too far abducted│     │ · Measure sound vs prost length
└───────────────────────────┘      └───────────────────────────────────┘     └────────────────────────────┘
```

---

## 9. Orthotic Gait Analysis Module

Designed for patients utilizing Ankle-Foot Orthoses (AFO), Knee-Ankle-Foot Orthoses (KAFO), Supra-Malleolar Orthoses (SMO), or UCBL inserts.

### Quantifying Pre- vs. Post-Intervention Kinematics

```
  BAREFOOT ASSESSMENT                       AFO INTERVENTION ASSESSMENT              QUANTITATIVE COMPARISON
┌───────────────────────────┐             ┌───────────────────────────┐            ┌───────────────────────────┐
│ Knee Recurvatum: -12.4°   │  ─────────► │ Knee Recurvatum: -3.1°    │ ─────────► │ Recurvatum reduced by     │
│ Peak Swing DF: -8.2°      │             │ Peak Swing DF: +2.5°      │            │ 75% (9.3° correction).    │
└───────────────────────────┘             └───────────────────────────┘            └───────────────────────────┘
```

---

## 10. Clinical Hypothesis & Reasoning Engine

Every finding outputs a structured schema prioritizing candidates and recommending manual confirmation steps.

### Hypothesis JSON Schema Output
```json
{
  "finding_id": "FIND-88210",
  "deviation_code": "DEV-02",
  "label": "Reduced Ankle Dorsiflexion During Swing",
  "side": "left",
  "phase": "Mid-Swing (75-87%)",
  "severity": "moderate",
  "evidence": {
    "observed_value": -6.5,
    "unit": "degrees",
    "reference_range": [2.0, 10.0],
    "cycles_affected_count": 8,
    "total_cycles_analyzed": 8
  },
  "candidate_contributors": [
    {
      "rank": 1,
      "category": "musculoskeletal_weakness",
      "description": "Anterior Tibialis Weakness / Foot Drop pattern",
      "likelihood": "high"
    },
    {
      "rank": 2,
      "category": "joint_limitation",
      "description": "Gastrocnemius-Soleus Contracture / Structural Ankle Equinus",
      "likelihood": "moderate"
    },
    {
      "rank": 3,
      "category": "orthotic_factor",
      "description": "Inadequate AFO Dorsiflexion Assist or Plantarflexion Stop",
      "likelihood": "moderate"
    }
  ],
  "recommended_clinical_checks": [
    "Manual Muscle Testing (MMT) of Tibialis Anterior (Deep Peroneal Nerve / L4-L5)",
    "Silfverskiöld Test to isolate Gastrocnemius vs. Soleus tightness",
    "Passive Ankle Dorsiflexion Range of Motion measurement with knee extended and flexed",
    "Inspection of AFO ankle joint stiffness setting or plantarflexion stop alignment"
  ],
  "confidence_scores": {
    "movement_detection_confidence": 0.94,
    "biomechanical_interpretation_confidence": 0.82,
    "etiological_hypothesis_confidence": 0.58
  }
}
```

---

## 11. AI Architecture & Modular Pipeline

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   GAITINTEL PIPELINE                                   │
│                                                                                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────────┐  │
│  │ Video Upload │ ──► │ MediaPipe    │ ──► │ Landmark     │ ──► │ Gait Event        │  │
│  │ & Preprocess │     │ Pose Extractor│    │ Smoothing    │     │ Detection Engine  │  │
│  └──────────────┘     └──────────────┘     └──────────────┘     └─────────┬─────────┘  │
│                                                                           │            │
│                                                                           ▼            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────────┐  │
│  │ Clinical     │ ◄── │ Reasoning    │ ◄── │ Deviation    │ ◄── │ Joint Kinematic   │  │
│  │ Dashboard UI │     │ Engine       │     │ Evaluator    │     │ Calculation Engine│  │
│  └──────────────┘     └──────────────┘     └──────────────┘     └───────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Explainable AI (XAI) & Evidence Lineage

To ensure clinician confidence and prevent black-box decisions, GaitIntel links every candidate directly back to raw measured evidence.

```
+---------------------------------------------------------------------------------------+
|                                EXPLAINABILITY TRACE                                   |
|                                                                                       |
|  CANDIDATE HYPOTHESIS: Possible Left Quadriceps Weakness                             |
|                                                                                       |
|  MEASURED EVIDENCE TRACE:                                                             |
|  1. Left Knee Flexion during Loading Response = 24.1° (Expected: 15.0° - 18.0°).      |
|  2. Compensatory Forward Trunk Lean = 11.2° during mid-stance.                        |
|  3. Ipsilateral Stance Duration reduced by 18% compared to sound right limb.          |
|  4. Pattern repeated reliably across 6 consecutive gait cycles (p < 0.01).            |
+---------------------------------------------------------------------------------------+
```

---

## 13. Gait Training Target Generator

Generates prioritized, non-prescriptive exercise and gait-retraining options.

```
                    ┌──────────────────────────────────────┐
                    │      Detected Gait Abnormalities     │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │      Target Generator Engine         │
                    └──────────────────┬───────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│ Training Target  │          │ Training Target  │          │ Training Target  │
│ Swing Clearance  │          │ Trunk Control    │          │ Step Symmetry    │
└────────┬─────────┘          └────────┬─────────┘          └────────┬─────────┘
         │                             │                             │
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│ Suggested Option │          │ Suggested Option │          │ Suggested Option │
│ · Active DF      │          │ · Mirror Feedback│          │ · Auditory Cues  │
│   drills         │          │ · Abductor strength│        │ · Treadmill step │
└──────────────────┘          └──────────────────┘          └──────────────────┘
```

---

## 14. Comparative Analytics (Before/After & Intervention Tracking)

GaitIntel computes exact deltas, percentage shifts, and statistical confidence intervals across paired assessments.

### Comparative Output Metrics
$$\Delta \theta = \theta_{\text{post}} - \theta_{\text{pre}}$$

$$\% \text{ Change} = \left( \frac{\theta_{\text{post}} - \theta_{\text{pre}}}{\theta_{\text{pre}}} \right) \times 100$$

| Metric Parameter | Baseline (Pre-Intervention) | Follow-Up (Post-Intervention) | Delta ($\Delta$) | Direction & Clinical Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Walking Speed** | $0.82\text{ m/s}$ | $1.05\text{ m/s}$ | $+0.23\text{ m/s}$ | $+28.0\%$ (Improved functional mobility) |
| **Step Asymmetry (ASI)**| $22.4\%$ | $8.1\%$ | $-14.3\%$ | $-63.8\%$ (Improved bilateral symmetry) |
| **Knee Recurvatum** | $-11.2^{\circ}$ | $-2.1^{\circ}$ | $+9.1^{\circ}$ | $81.2\%$ reduction in hyperextension |

---

## 15. Visualization & Interactive Kinematic Dashboard

### Dashboard Interface Components
1. **Video Player Canvas:** Synchronized pose skeleton overlay with play/pause, frame-by-frame scrubbing, and angle annotations.
2. **Normalized Gait Cycle Graphs (0-100%):**
   * Hip Flexion/Extension trajectory curves.
   * Knee Flexion/Extension trajectory curves.
   * Ankle Dorsiflexion/Plantarflexion trajectory curves.
   * Shaded normative corridors for clinical reference comparison.
3. **Left vs. Right Overlay:** Direct visual comparison of affected vs. sound limb trajectories.

---

## 16. Composite Gait Deviation Scoring Framework

GaitIntel calculates interpretable sub-scores ($0-100\%$) representing biomechanical quality.

### Mathematical Sub-Score Formulations
* **Temporal Symmetry Score ($S_{\text{temp}}$):**
  $$S_{\text{temp}} = 100 \times \left(1 - \frac{|t_{\text{stance, L}} - t_{\text{stance, R}}|}{t_{\text{stance, L}} + t_{\text{stance, R}}}\right)$$

* **Knee Control Score ($S_{\text{knee}}$):**
  $$S_{\text{knee}} = 100 - \sum_{i \in \text{cycles}} \left( w_1 \cdot \text{RecurvatumDeg}_i + w_2 \cdot \text{SwingFlexDeficit}_i \right)$$

```
Gait Symmetry        ████████████████████░░░░  82%
Temporal Symmetry    █████████████████░░░░░░░  71%
Knee Joint Control   ███████████████░░░░░░░░░  63%
Ankle Joint Control  █████████████░░░░░░░░░░░  54%
Pelvic Stability     ███████████████████░░░░░  79%
```

---

## 17. Longitudinal Patient Timeline

Tracks a patient's functional progress across multiple clinical visits and intervention milestones.

```
  VISIT 1 (2026-01-10)               INTERVENTION (2026-02-01)              VISIT 2 (2026-03-15)
┌───────────────────────┐          ┌───────────────────────────┐          ┌───────────────────────┐
│ Baseline Evaluation   │ ───────► │ Rigid AFO Fitted with     │ ───────► │ Follow-up Evaluation  │
│ Speed: 0.75 m/s       │          │ 5° Plantarflexion Stop    │          │ Speed: 0.98 m/s       │
│ Asymmetry: 26%        │          └───────────────────────────┘          │ Asymmetry: 9%         │
└───────────────────────┘                                                 └───────────────────────┘
```

---

## 18. Clinician Dashboard Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CLINICAL WORKFLOW                                     │
│                                                                                         │
│  1. Patient Selection ──► 2. Video Upload ──► 3. Automated Analysis ──► 4. Kinematic   │
│     & Metadata Entry         & Pose Pipeline     & Event Detection         Graph Review │
│                                                                                 │       │
│                                                                                 ▼       │
│  7. PDF Export &      ◄── 6. Clinical        ◄── 5. Review Candidate ◄─────────────────┘       │
│     EMR Save              Documentation          Findings & Recommendations             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 19. Automated Clinical Report Engine

Generates a structured clinical report ready for signature and insertion into Electronic Health Record (EHR) systems.

```
================================================================================
                       GAITINTEL CLINICAL ANALYSIS REPORT
================================================================================
PATIENT ID: P-98402                 ASSESSMENT DATE: 2026-09-05
AGE: 48 | SEX: Female               ASSESSOR: Dr. J. Vance, CPO
DEVICE: Rigid AFO (Left Limb)       SIDE ANALYZED: Bilateral
--------------------------------------------------------------------------------

1. OBSERVED KINEMATIC DEVIATIONS
   • Left Ankle Dorsiflexion Deficit during Mid-Swing (-6.5° vs +5.0° Normative)
   • Right Compensatory Lateral Trunk Lean (9.2° Stance Lean)
   • Step Duration Asymmetry Index: 18.4%

2. BIOMECHANICAL INTERPRETATION
   The observed movement pattern displays reduced swing-phase clearance on the left
   lower extremity, accompanied by contralateral trunk lean to facilitate toe clearance.

3. CANDIDATE CONTRIBUTORS FOR CLINICIAN REVIEW
   [1] Left Dorsiflexor Weakness (e.g., L4-L5 radiculopathy or peroneal nerve injury)
   [2] Inadequate AFO Dorsiflexion Assistance setting
   [3] Plantarflexion Contracture / Gastrocnemius Tightness

4. RECOMMENDED CLINICAL ASSESSMENTS
   [ ] Manual Muscle Test: Left Anterior Tibialis & Peroneus Longus
   [ ] Passive Range of Motion: Left Ankle Joint (Goniometric measurement)
   [ ] Orthotic Inspection: Assess AFO hinge alignment and shoe heel height

5. CLINICIAN DOCUMENTATION & NOTES
   Clinician Notes: ___________________________________________________________

--------------------------------------------------------------------------------
IMPORTANT CLINICAL NOTICE:
"AI-generated findings are clinical decision-support information and do not
constitute a medical diagnosis. Final interpretations and treatment decisions
must be rendered by a qualified licensed clinician."
================================================================================
```

---

## 20. Data Architecture & Model Fine-Tuning Persistence

GaitIntel captures structured biomechanical records to enable ongoing model refinement.

### Database Schema Entity Relationships

```
┌──────────────┐       1:N       ┌─────────────────┐       1:N       ┌──────────────┐
│   Patient    │ ───────────────►│   Assessment    │ ───────────────►│  GaitVideo   │
└──────────────┘                 └────────┬────────┘                 └──────────────┘
                                          │
                                          │ 1:1
                                          ▼
                                 ┌─────────────────┐       1:N       ┌──────────────┐
                                 │   GaitCycle     │ ───────────────►│  JointAngle  │
                                 └────────┬────────┘                 └──────────────┘
                                          │
                                          │ 1:N
                                          ▼
                                 ┌─────────────────┐
                                 │   GaitFinding   │
                                 └─────────────────┘
```

---

## 21. Research Mode & Analytics Export Engine

Provides researchers and P&O educators with raw, un-aggregated kinematic coordinates, angle time-series, and model validation tools.

### Supported Export Formats
* **Time-Series CSV:** Frame-by-frame joint angles, raw 3D landmark coordinates ($x, y, z$), and ground-truth gait events.
* **JSON Schema:** Complete assessment payload including metadata, cycle boundaries, and findings graph.

### Research Model Evaluation Suite
* Confusion Matrix generation for deviation classifiers.
* ROC-AUC, Precision, Recall, F1-Score, Sensitivity, and Specificity metrics.
* Automatic patient de-identification conforming to HIPAA Safe Harbor guidelines.

---

## 22. Technology Stack & System Integration

```
       ┌──────────────────────────────────────────────────────────┐
       │                       FRONTEND                           │
       │ Next.js 14 (App Router), TypeScript, Tailwind, Recharts │
       └────────────────────────────┬─────────────────────────────┘
                                    │ REST API / WebSockets
       ┌────────────────────────────▼─────────────────────────────┐
       │                       BACKEND                            │
       │       Python 3.11+, FastAPI, Uvicorn Async Server        │
       └──────┬─────────────────────┬────────────────────┬────────┘
              │                     │                    │
┌─────────────▼──────────┐ ┌────────▼─────────┐ ┌────────▼──────────────┐
│  CV & Pose Pipeline    │ │ Kinematic Math   │ │ Reasoning Engine     │
│  OpenCV, MediaPipe     │ │ NumPy, SciPy     │ │ JSON Knowledge Base  │
└─────────────┬──────────┘ └────────┬─────────┘ └────────┬──────────────┘
              │                     │                    │
              └─────────────────────┼────────────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │   POSTGRESQL DATABASE   │
                       │ Supabase / Local Docker │
                       └─────────────────────────┘
```

---

## 23. MVP Development Strategy (V1 to V7 Roadmap)

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│    V1    │──▶│    V2    │──▶│    V3    │──▶│    V4    │──▶│    V5    │──▶│    V6    │──▶│    V7    │
│ Core MVP │   │Prosthetic│   │ Orthotic │   │ Temporal │   │ Multi-Cam│   │ Sensors  │   │ Clinical │
│ Pipeline │   │ Module   │   │ Module   │   │ ML Model │   │ 3D Gait  │   │ IMU/Press│   │ Trial    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

* **V1 (Core MVP):** Video upload, MediaPipe pose extraction, 2D sagittal joint angles, gait event detection, 10 rule-based deviation detectors, seed knowledge engine, clinical dashboard.
* **V2 (Prosthetic Gait Module):** Prosthetic socket fit & alignment reasoning engine, sound vs. prosthetic limb comparison, PDF clinical report generator.
* **V3 (Orthotic Gait Module):** Pre/Post orthotic intervention comparative module, AFO stiffness evaluation, kinematic diff overlays.
* **V4 (Temporal Deep Learning):** 1D-CNN / LSTM / Temporal Convolutional Networks trained on annotated clinical dataset.
* **V5 (Multi-Camera 3D Analysis & Research Mode):** Multi-camera view triangulation, 3D kinematic estimation, CSV/JSON research exporter.
* **V6 (Multi-Modal Sensor Integration):** Synchronized IMU wearable sensor and force plate / in-shoe pressure plate integration.
* **V7 (Clinical Validation & Deployment):** Multi-site prospective clinical validation, regulatory SaMD documentation, local on-device inference mode.

---

## 24. Clinical Safety, Auditability & Validation Protocols

### System Audit Trail Schema
Every clinician edit, finding override, or note entry is recorded in an immutable audit ledger:

```json
{
  "audit_id": "AUD-99104",
  "assessment_id": "ASM-3019",
  "timestamp": "2026-09-05T15:10:22Z",
  "clinician_id": "USER-4402",
  "action": "OVERRIDE_FINDING_CANDIDATE",
  "target_finding_id": "FIND-88210",
  "original_state": {
    "top_candidate": "Anterior Tibialis Weakness"
  },
  "modified_state": {
    "top_candidate": "Gastrocnemius Contracture",
    "override_reason": "Manual Range of Motion confirmed severe passive dorsiflexion restriction (+0 deg max)."
  }
}
```

### Safety Safeguards
1. **Separation of Concerns:** Algorithmic movement detection is strictly decoupled from candidate hypothesis generation.
2. **Confidence Indicators:** Confidence scores are segmented into Detection Confidence, Biomechanical Interpretation Confidence, and Etiological Hypothesis Confidence.
3. **Local On-Device Inference Option:** For privacy-sensitive healthcare environments, video inference can run entirely within the local clinic network without transmitting media to public cloud servers.
