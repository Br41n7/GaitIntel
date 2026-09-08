"""
Gait event detection: initial contact (heel strike) and toe-off, per
side, from 2D landmark trajectories alone (no force plate).

Method: the horizontal (x) position of the ankle relative to the hip,
in the direction of walking. When the foot lands out in front of the
body (initial contact), this reaches a local extreme in the direction
of travel; when the foot is about to leave the ground behind the body
(toe-off), it reaches the opposite extreme. This is a standard
kinematic proxy for gait events without instrumented ground contact
(see Zeni et al., 2008, "Two simple methods for determining gait
events during treadmill and overground walking using kinematic data") —
adequate for MVP; a force-sensitive or vertical-velocity-based method
would be more precise but needs data this pipeline doesn't have.

Walking direction is auto-detected from the hip's net horizontal
displacement across the clip, so this works regardless of whether the
subject walks left-to-right or right-to-left in frame.
"""
from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks

from app.pipeline.gait_types import GaitFrame, Side

MIN_STEP_INTERVAL_S = 0.25  # reject events closer together than a plausible fastest step


@dataclass
class GaitEvents:
    side: Side
    initial_contacts: list[int]  # frame indices
    toe_offs: list[int]  # frame indices


def _hip_ankle_series(frames: list[GaitFrame], side: Side) -> tuple[list[int], list[float], list[float]]:
    """Returns (frame_indices, timestamps, ankle_x_minus_hip_x) for
    frames where both landmarks are present."""
    hip_name, ankle_name = f"{side.value}_hip", f"{side.value}_ankle"
    frame_indices, timestamps, relative_x = [], [], []

    for frame in frames:
        hip = frame.landmarks.get(hip_name)
        ankle = frame.landmarks.get(ankle_name)
        if hip is None or ankle is None:
            continue
        frame_indices.append(frame.frame_index)
        timestamps.append(frame.timestamp_s)
        relative_x.append(ankle.x - hip.x)

    return frame_indices, timestamps, relative_x


def detect_gait_events(frames: list[GaitFrame], side: Side, fps: float) -> GaitEvents:
    frame_indices, timestamps, relative_x = _hip_ankle_series(frames, side)

    if len(relative_x) < 3:
        return GaitEvents(side=side, initial_contacts=[], toe_offs=[])

    # Direction of travel: positive if the subject moves toward
    # increasing x (rightward in frame) over the clip, negative otherwise.
    hip_xs = [frame.landmarks[f"{side.value}_hip"].x for frame in frames if f"{side.value}_hip" in frame.landmarks]
    direction = 1.0 if (hip_xs[-1] - hip_xs[0]) >= 0 else -1.0

    signal = np.array(relative_x) * direction
    min_distance_frames = max(1, int(MIN_STEP_INTERVAL_S * fps))

    ic_peak_indices, _ = find_peaks(signal, distance=min_distance_frames)
    to_peak_indices, _ = find_peaks(-signal, distance=min_distance_frames)

    initial_contacts = [frame_indices[i] for i in ic_peak_indices]
    toe_offs = [frame_indices[i] for i in to_peak_indices]

    return GaitEvents(side=side, initial_contacts=initial_contacts, toe_offs=toe_offs)
