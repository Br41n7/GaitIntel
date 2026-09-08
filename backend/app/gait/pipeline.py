"""
Orchestrates Phase 3: takes the raw pose_data already stored on an
Assessment (see app/api/pose.py) and produces real GaitMetrics plus
normalized joint-angle trajectories for charting.

Deliberately does NOT produce deviation findings — that's Phase 4
(the 10 deterministic detectors), a separate, not-yet-built step. This
function's output plugs into analysis.py in place of the metrics half
of the old stub; the findings half stays explicitly stubbed until
Phase 4 lands, rather than being quietly backfilled with a couple of
ad-hoc checks that would blur the phase boundary.
"""
from dataclasses import asdict

from app.gait.angles import compute_raw_angle_series, resample_to_percent_cycle
from app.gait.cycles import build_gait_cycles
from app.gait.events import detect_gait_events
from app.pipeline.gait_types import GaitFrame, Landmark, Side
from app.gait.metrics import compute_gait_metrics

MIN_FRAMES_WITH_POSE = 10
JOINTS = ("hip", "knee", "ankle")


class GaitAnalysisError(ValueError):
    pass


def _frames_from_pose_data(pose_data: dict) -> list[GaitFrame]:
    frames = []
    for raw in pose_data.get("frames", []):
        landmarks = {
            name: Landmark(**lm) for name, lm in raw.get("landmarks", {}).items()
        }
        frames.append(
            GaitFrame(
                frame_index=raw["frame_index"],
                timestamp_s=raw["timestamp_s"],
                landmarks=landmarks,
            )
        )
    return frames


def run_gait_analysis(pose_data: dict, fps: float) -> dict:
    frames = _frames_from_pose_data(pose_data)

    frames_with_pose = [f for f in frames if f.landmarks]
    if len(frames_with_pose) < MIN_FRAMES_WITH_POSE:
        raise GaitAnalysisError(
            f"Too few frames with detected pose ({len(frames_with_pose)}) to compute gait "
            f"metrics — need at least {MIN_FRAMES_WITH_POSE}. Check that the video clearly "
            "shows a full-body sagittal view of someone walking."
        )

    duration_s = frames[-1].timestamp_s - frames[0].timestamp_s if len(frames) > 1 else 0.0

    events_by_side = {
        Side.left: detect_gait_events(frames, Side.left, fps),
        Side.right: detect_gait_events(frames, Side.right, fps),
    }

    raw_angle_series = {}
    normalized_angle_series = []
    for joint in JOINTS:
        for side in (Side.left, Side.right):
            raw = compute_raw_angle_series(frames, joint, side)
            raw_angle_series[(joint, side)] = raw
            if raw.angle_degrees:
                normalized_angle_series.append(asdict(resample_to_percent_cycle(raw)))

    metrics = compute_gait_metrics(events_by_side, raw_angle_series, fps, duration_s)

    gait_cycles = {
        side.value: [asdict(c) for c in build_gait_cycles(frames, events, fps)]
        for side, events in events_by_side.items()
    }

    return {
        "metrics": asdict(metrics),
        "joint_angle_trajectories": normalized_angle_series,
        "gait_cycles": gait_cycles,
        "events": {
            side.value: {"initial_contacts": e.initial_contacts, "toe_offs": e.toe_offs}
            for side, e in events_by_side.items()
        },
    }
