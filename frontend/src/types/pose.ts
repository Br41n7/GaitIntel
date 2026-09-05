export interface PoseFrame {
  frame_index: number;
  timestamp_s: number;
  landmarks: Record<string, { x: number; y: number; z: number | null; visibility: number | null }>;
}

// Bones to draw between named landmarks — mirrors backend/app/pose/landmarks.py.
// Keep this list in sync manually for v0.1; it's small enough that codegen
// isn't worth the setup yet.
export const SKELETON_CONNECTIONS: [string, string][] = [
  ["left_shoulder", "left_hip"],
  ["right_shoulder", "right_hip"],
  ["left_hip", "right_hip"],
  ["left_hip", "left_knee"],
  ["left_knee", "left_ankle"],
  ["left_ankle", "left_heel"],
  ["left_ankle", "left_toe"],
  ["left_heel", "left_toe"],
  ["right_hip", "right_knee"],
  ["right_knee", "right_ankle"],
  ["right_ankle", "right_heel"],
  ["right_ankle", "right_toe"],
  ["right_heel", "right_toe"],
];
