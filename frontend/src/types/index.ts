// Mirrors backend/app/pipeline/types.py and schemas/*.py.
// Keep these in sync by hand for v0.1 — codegen (openapi-typescript)
// is worth adding once the API surface stabilizes past Phase 1.

export type Side = "left" | "right";

export type Phase =
  | "initial_contact"
  | "loading_response"
  | "mid_stance"
  | "terminal_stance"
  | "pre_swing"
  | "initial_swing"
  | "mid_swing"
  | "terminal_swing"
  | "stance"
  | "swing";

export type AssessmentStatus =
  | "created"
  | "video_uploaded"
  | "pose_extracting"
  | "pose_extracted"
  | "analyzing"
  | "analyzed"
  | "reviewed"
  | "failed";

export interface Patient {
  id: string;
  identifier: string;
  display_name: string | null;
  date_of_birth: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface GaitMetrics {
  cadence_steps_per_min: number | null;
  left_stance_time_s: number | null;
  right_stance_time_s: number | null;
  left_swing_time_s: number | null;
  right_swing_time_s: number | null;
  step_asymmetry: number | null;
  stance_asymmetry: number | null;
  left_knee_rom_deg: number | null;
  right_knee_rom_deg: number | null;
  left_hip_rom_deg: number | null;
  right_hip_rom_deg: number | null;
  left_ankle_rom_deg: number | null;
  right_ankle_rom_deg: number | null;
  walking_velocity_m_s: number | null;
}

export interface GaitFinding {
  id: string;
  side: Side;
  phase: Phase;
  value: number;
  unit: string;
  threshold: number | null;
  confidence: number; // detection confidence only
  evidence: string[];
}

export interface ClinicalHypothesis {
  finding_id: string;
  possible_contributors: { id: string; priority: number; description: string }[];
  clinical_assessments: { id: string; name: string }[];
  training_targets: { id: string; name: string }[];
  interpretation_confidence: "low" | "moderate" | "high";
  knowledge_version: string;
}

export interface FindingWithKnowledge {
  finding: GaitFinding;
  clinical_hypothesis: ClinicalHypothesis;
}

export interface JointAngleTrajectory {
  joint: "hip" | "knee" | "ankle";
  side: Side;
  percent_gait_cycle: number[];
  angle_degrees: number[];
}

export interface AssessmentResults {
  metrics: GaitMetrics;
  joint_angle_trajectories: JointAngleTrajectory[];
  gait_cycles: Record<string, unknown>;
  events: Record<string, { initial_contacts: number[]; toe_offs: number[] }>;
  findings: FindingWithKnowledge[];
  findings_status: string | null; // e.g. "Deviation detection is not implemented yet (Phase 4)."
  analysis_version: string;
}

export interface Assessment {
  id: string;
  patient_id: string;
  status: AssessmentStatus;
  video_original_filename: string | null;
  video_storage_key: string | null;
  video_fps: number | null;
  video_duration_s: number | null;
  video_width: number | null;
  video_height: number | null;
  results: AssessmentResults | null;
  clinician_notes: string | null;
  error_message: string | null;
  analysis_version: string | null;
  knowledge_version: string | null;
  created_at: string;
  updated_at: string;
}
