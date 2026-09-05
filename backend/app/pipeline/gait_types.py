"""
Internal data contracts. Every external library (MediaPipe today,
MyoGait/RTMPose/whatever later) gets converted into these shapes at
the adapter boundary. Nothing downstream of the adapter — gait math,
deviation detection, the knowledge engine, or the frontend — is ever
allowed to see a raw MediaPipe/vendor object.

If you're tempted to reach for `landmarks.pose_landmarks[0].x` outside
of a *Provider class, stop: that means the boundary is leaking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(str, Enum):
    left = "left"
    right = "right"


class Phase(str, Enum):
    initial_contact = "initial_contact"
    loading_response = "loading_response"
    mid_stance = "mid_stance"
    terminal_stance = "terminal_stance"
    pre_swing = "pre_swing"
    initial_swing = "initial_swing"
    mid_swing = "mid_swing"
    terminal_swing = "terminal_swing"
    stance = "stance"  # coarse fallback when sub-phase isn't resolved
    swing = "swing"


@dataclass
class Landmark:
    x: float
    y: float
    z: float | None = None
    visibility: float | None = None  # 0-1, how confident the pose model is in this point


@dataclass
class GaitFrame:
    """One video frame's worth of pose data, already converted from
    whatever the pose provider returned into named joints."""
    frame_index: int
    timestamp_s: float
    landmarks: dict[str, Landmark] = field(default_factory=dict)  # e.g. "left_hip", "right_knee"


@dataclass
class GaitCycle:
    """One full gait cycle for one side: initial contact to next
    initial contact, normalized to 0-100%."""
    side: Side
    start_frame: int
    end_frame: int
    start_time_s: float
    end_time_s: float
    percent_normalized_frame_indices: list[int] = field(default_factory=list)


@dataclass
class JointAngleSeries:
    """One joint's angle across a normalized 0-100% gait cycle."""
    joint: str  # "hip" | "knee" | "ankle"
    side: Side
    percent_gait_cycle: list[float]  # 0-100, evenly spaced
    angle_degrees: list[float]


@dataclass
class JointAngles:
    hip: list[JointAngleSeries] = field(default_factory=list)
    knee: list[JointAngleSeries] = field(default_factory=list)
    ankle: list[JointAngleSeries] = field(default_factory=list)


@dataclass
class GaitMetrics:
    cadence_steps_per_min: float | None = None
    left_step_time_s: float | None = None
    right_step_time_s: float | None = None
    left_stride_time_s: float | None = None
    right_stride_time_s: float | None = None
    left_stance_time_s: float | None = None
    right_stance_time_s: float | None = None
    left_swing_time_s: float | None = None
    right_swing_time_s: float | None = None
    double_support_time_s: float | None = None
    walking_velocity_m_s: float | None = None  # only when camera setup permits
    step_asymmetry: float | None = None  # 0-1
    stance_asymmetry: float | None = None  # 0-1
    left_knee_rom_deg: float | None = None
    right_knee_rom_deg: float | None = None
    left_hip_rom_deg: float | None = None
    right_hip_rom_deg: float | None = None
    left_ankle_rom_deg: float | None = None
    right_ankle_rom_deg: float | None = None


@dataclass
class GaitFinding:
    """One deviation flagged by a detector. `confidence` here is
    DETECTION confidence only (how sure we are the measurement is
    real) — never conflate this with clinical interpretation
    confidence, which lives in ClinicalHypothesis instead."""
    id: str  # e.g. "knee_hyperextension"
    side: Side
    phase: Phase
    value: float
    unit: str
    threshold: float | None = None
    confidence: float = 0.0  # 0-1, detection confidence
    evidence: list[str] = field(default_factory=list)


@dataclass
class ClinicalHypothesis:
    """Output of the ClinicalKnowledgeEngine for one finding. This is
    deliberately NOT a diagnosis — see knowledge_engine.py."""
    finding_id: str
    possible_contributors: list[dict] = field(default_factory=list)
    clinical_assessments: list[dict] = field(default_factory=list)
    training_targets: list[dict] = field(default_factory=list)
    interpretation_confidence: str = "moderate"  # "low" | "moderate" | "high" — separate from detection confidence
    knowledge_version: str = "0.1.0"


@dataclass
class Recommendation:
    """Reserved for the future prosthetic/orthotic modules — a
    'consider evaluating X' item, never an automatic instruction."""
    id: str
    description: str
    category: str  # e.g. "prosthetic_alignment", "training_target"
