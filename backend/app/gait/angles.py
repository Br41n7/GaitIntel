"""
Joint-angle calculation from landmark triples.

Uses 2D (x, y) coordinates only — MediaPipe's z estimate is unreliable
from a single camera and would add noise, not signal, for a sagittal-
plane walking video. If a future PoseProvider gives genuinely reliable
depth (stereo rig, depth camera), this can be extended to 3D without
changing the call signature.

Angle convention: `calculate_angle(a, b, c)` returns the interior angle
at vertex B in degrees (0-180). For joint "flexion" angles (hip, knee,
ankle) we report `180 - interior_angle` instead, so a fully extended
(straight) joint reads as ~0° and flexion increases from there — this
matches how clinicians usually think about joint angles, rather than
raw computational-geometry interior angles.
"""
import math
from dataclasses import dataclass

from app.pipeline.gait_types import GaitFrame, JointAngleSeries, Side


def calculate_angle(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    """Interior angle at vertex B, in degrees, given three 2D points."""
    ux, uy = a[0] - b[0], a[1] - b[1]
    vx, vy = c[0] - b[0], c[1] - b[1]

    dot = ux * vx + uy * vy
    mag_u = math.hypot(ux, uy)
    mag_v = math.hypot(vx, vy)

    if mag_u == 0 or mag_v == 0:
        return 0.0

    cos_angle = max(-1.0, min(1.0, dot / (mag_u * mag_v)))
    return math.degrees(math.acos(cos_angle))


# (proximal, vertex, distal) landmark names per joint, per side.
# Hip uses the shoulder as the proximal point (trunk-thigh angle) since
# there's no landmark "above" the hip that better represents trunk
# orientation without adding a spine model.
JOINT_LANDMARK_TRIPLES = {
    "hip": ("{side}_shoulder", "{side}_hip", "{side}_knee"),
    "knee": ("{side}_hip", "{side}_knee", "{side}_ankle"),
    "ankle": ("{side}_knee", "{side}_ankle", "{side}_toe"),
}


def _point(frame: GaitFrame, name: str) -> tuple[float, float] | None:
    lm = frame.landmarks.get(name)
    if lm is None:
        return None
    return (lm.x, lm.y)


@dataclass
class RawAngleSeries:
    """Per-frame angle series, still tied to raw frame indices/timestamps
    — the intermediate form used for event detection and ROM
    calculation, before it's resampled onto a normalized 0-100% gait
    cycle for charting (see cycles.py for that step)."""
    joint: str
    side: Side
    frame_indices: list[int]
    timestamps_s: list[float]
    angle_degrees: list[float]


def compute_raw_angle_series(frames: list[GaitFrame], joint: str, side: Side) -> RawAngleSeries:
    """Angle at every frame where all three landmarks are present.
    Frames with missing landmarks are skipped rather than interpolated
    — smoothing/hold-last-good already happened at the pose-extraction
    stage; skipping here just means we don't fabricate an angle when
    even the smoothed pose has no data for that landmark."""
    proximal_name, vertex_name, distal_name = (
        t.format(side=side.value) for t in JOINT_LANDMARK_TRIPLES[joint]
    )

    frame_indices: list[int] = []
    timestamps_s: list[float] = []
    angle_degrees: list[float] = []

    for frame in frames:
        a, b, c = _point(frame, proximal_name), _point(frame, vertex_name), _point(frame, distal_name)
        if a is None or b is None or c is None:
            continue
        interior = calculate_angle(a, b, c)
        angle_degrees.append(180.0 - interior)  # flexion convention — see module docstring
        frame_indices.append(frame.frame_index)
        timestamps_s.append(frame.timestamp_s)

    return RawAngleSeries(
        joint=joint, side=side, frame_indices=frame_indices, timestamps_s=timestamps_s, angle_degrees=angle_degrees
    )


def resample_to_percent_cycle(raw: RawAngleSeries, num_points: int = 101) -> JointAngleSeries:
    """Resample a raw angle series onto an evenly-spaced 0-100% grid for
    charting. Uses simple linear interpolation over the raw series'
    own frame range — this is a whole-clip resampling, not a per-cycle
    average across multiple strides; see metrics.py's ROM calculation
    for the same caveat applied to range-of-motion."""
    import numpy as np

    if len(raw.frame_indices) < 2:
        return JointAngleSeries(joint=raw.joint, side=raw.side, percent_gait_cycle=[], angle_degrees=[])

    x = np.array(raw.frame_indices, dtype=float)
    y = np.array(raw.angle_degrees, dtype=float)
    x_norm = (x - x[0]) / (x[-1] - x[0]) * 100.0
    percent_grid = np.linspace(0, 100, num_points)
    resampled = np.interp(percent_grid, x_norm, y)

    return JointAngleSeries(
        joint=raw.joint,
        side=raw.side,
        percent_gait_cycle=percent_grid.tolist(),
        angle_degrees=resampled.tolist(),
    )
