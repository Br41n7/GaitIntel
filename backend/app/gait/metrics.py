"""
Computes GaitMetrics from detected events and angle series.

Every field here is either a real computed value or explicitly None —
nothing is estimated or guessed to fill a field the input data can't
actually support. In particular:

- `walking_velocity_m_s` is always None in v0.1: landmark coordinates
  are normalized 0-1 image-space, not real-world units, and there's no
  camera calibration step to convert one to the other. Filling this in
  with a guessed conversion factor would be worse than leaving it out.
- `double_support_time_s` uses a standard approximation (see the
  function docstring) rather than true bilateral stance overlap, which
  would need both feet's contact intervals reconciled more carefully
  than v0.1's event detector currently does.
"""
import statistics

from app.gait.angles import RawAngleSeries
from app.gait.events import GaitEvents
from app.pipeline.gait_types import GaitMetrics, Side


def _pair_stance_swing(events: GaitEvents) -> tuple[list[float], list[float]]:
    """For each IC, find the next TO (stance duration) and the IC after
    that (swing duration). Returns (stance_durations_frames, swing_durations_frames)
    — caller converts to seconds using fps."""
    stance_frames: list[float] = []
    swing_frames: list[float] = []

    ics = sorted(events.initial_contacts)
    tos = sorted(events.toe_offs)

    for i, ic in enumerate(ics):
        next_ic = ics[i + 1] if i + 1 < len(ics) else None
        # first TO that falls between this IC and the next one
        matching_to = next((to for to in tos if ic < to < (next_ic or float("inf"))), None)
        if matching_to is None:
            continue
        stance_frames.append(matching_to - ic)
        if next_ic is not None:
            swing_frames.append(next_ic - matching_to)

    return stance_frames, swing_frames


def _rom(raw_series: RawAngleSeries | None) -> float | None:
    """Whole-clip range of motion: max - min of the angle series. This
    is NOT a per-cycle-averaged ROM — a single noisy frame at either
    extreme will move this value more than a proper clinical ROM
    calculation would tolerate. Fine for v0.1; revisit if real footage
    shows this being thrown off by outlier frames."""
    if raw_series is None or len(raw_series.angle_degrees) < 2:
        return None
    return max(raw_series.angle_degrees) - min(raw_series.angle_degrees)


def compute_gait_metrics(
    events_by_side: dict[Side, GaitEvents],
    angle_series_by_key: dict[tuple[str, Side], RawAngleSeries],
    fps: float,
    duration_s: float,
) -> GaitMetrics:
    metrics = GaitMetrics()

    if fps <= 0:
        return metrics

    # Cadence: total initial-contact events across both sides, over
    # the clip's duration. Each IC is one footstep landing.
    total_ics = sum(len(e.initial_contacts) for e in events_by_side.values())
    if duration_s > 0:
        metrics.cadence_steps_per_min = round(total_ics / duration_s * 60, 1)

    for side in (Side.left, Side.right):
        events = events_by_side.get(side)
        if events is None:
            continue

        stance_frames, swing_frames = _pair_stance_swing(events)
        stance_s = [f / fps for f in stance_frames]
        swing_s = [f / fps for f in swing_frames]

        stride_frames = [b - a for a, b in zip(events.initial_contacts, events.initial_contacts[1:])]
        stride_s = [f / fps for f in stride_frames]

        if side == Side.left:
            metrics.left_stance_time_s = round(statistics.mean(stance_s), 3) if stance_s else None
            metrics.left_swing_time_s = round(statistics.mean(swing_s), 3) if swing_s else None
            metrics.left_stride_time_s = round(statistics.mean(stride_s), 3) if stride_s else None
        else:
            metrics.right_stance_time_s = round(statistics.mean(stance_s), 3) if stance_s else None
            metrics.right_swing_time_s = round(statistics.mean(swing_s), 3) if swing_s else None
            metrics.right_stride_time_s = round(statistics.mean(stride_s), 3) if stride_s else None

    # Step time: alternate-foot IC-to-IC interval, computed from the
    # interleaved sequence of both sides' initial contacts.
    all_ics = sorted(
        [(f, Side.left) for f in events_by_side.get(Side.left, GaitEvents(Side.left, [], [])).initial_contacts]
        + [(f, Side.right) for f in events_by_side.get(Side.right, GaitEvents(Side.right, [], [])).initial_contacts]
    )
    left_steps, right_steps = [], []
    for (f1, s1), (f2, s2) in zip(all_ics, all_ics[1:]):
        if s1 == s2:
            continue  # same-side consecutive detections shouldn't happen, skip defensively
        step_time = (f2 - f1) / fps
        # the step "belongs" to whichever foot just landed (s2)
        (left_steps if s2 == Side.left else right_steps).append(step_time)

    left_step_avg = statistics.mean(left_steps) if left_steps else None
    right_step_avg = statistics.mean(right_steps) if right_steps else None
    if left_step_avg:
        metrics.left_step_time_s = round(left_step_avg, 3)
    if right_step_avg:
        metrics.right_step_time_s = round(right_step_avg, 3)

    if left_step_avg and right_step_avg:
        mean_step = (left_step_avg + right_step_avg) / 2
        if mean_step > 0:
            metrics.step_asymmetry = round(abs(left_step_avg - right_step_avg) / mean_step, 3)

    if metrics.left_stance_time_s and metrics.right_stance_time_s:
        mean_stance = (metrics.left_stance_time_s + metrics.right_stance_time_s) / 2
        if mean_stance > 0:
            metrics.stance_asymmetry = round(
                abs(metrics.left_stance_time_s - metrics.right_stance_time_s) / mean_stance, 3
            )

    # Double support: standard approximation from stance-time overlap,
    # NOT true bilateral ground-contact reconciliation. See module docstring.
    if metrics.left_stance_time_s and metrics.right_stance_time_s and metrics.left_stride_time_s:
        combined_stance_pct = (
            (metrics.left_stance_time_s + metrics.right_stance_time_s) / metrics.left_stride_time_s
        ) * 100
        double_support_pct = max(0.0, combined_stance_pct - 100)
        metrics.double_support_time_s = round(double_support_pct / 100 * metrics.left_stride_time_s, 3)

    # ROM per joint, per side, from the raw (whole-clip) angle series.
    metrics.left_knee_rom_deg = _rom(angle_series_by_key.get(("knee", Side.left)))
    metrics.right_knee_rom_deg = _rom(angle_series_by_key.get(("knee", Side.right)))
    metrics.left_hip_rom_deg = _rom(angle_series_by_key.get(("hip", Side.left)))
    metrics.right_hip_rom_deg = _rom(angle_series_by_key.get(("hip", Side.right)))
    metrics.left_ankle_rom_deg = _rom(angle_series_by_key.get(("ankle", Side.left)))
    metrics.right_ankle_rom_deg = _rom(angle_series_by_key.get(("ankle", Side.right)))

    # walking_velocity_m_s intentionally left None — see module docstring.

    return metrics
