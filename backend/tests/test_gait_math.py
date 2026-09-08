"""
Validates the Phase 3 gait math against synthetic data with known
ground truth. A real walking video isn't available in every test
environment (CI, for instance, shouldn't depend on one), so these
tests construct landmark trajectories by hand where the correct
answer can be computed independently of the code under test.
"""
import math

import pytest

from app.gait.angles import calculate_angle, compute_raw_angle_series, resample_to_percent_cycle
from app.gait.cycles import build_gait_cycles
from app.gait.events import detect_gait_events
from app.gait.metrics import compute_gait_metrics
from app.pipeline.gait_types import GaitFrame, Landmark, Side


# ---------- calculate_angle: hand-verifiable geometry ----------

def test_calculate_angle_right_angle():
    # A directly above B, C directly right of B -> 90 degrees
    a, b, c = (0, 1), (0, 0), (1, 0)
    assert calculate_angle(a, b, c) == pytest.approx(90.0, abs=0.01)


def test_calculate_angle_straight_line():
    # A, B, C colinear with B between A and C -> 180 degrees (fully extended)
    a, b, c = (0, 1), (0, 0), (0, -1)
    assert calculate_angle(a, b, c) == pytest.approx(180.0, abs=0.01)


def test_calculate_angle_folded():
    # A and C on the same side of B -> 0 degrees (fully folded)
    a, b, c = (1, 0), (0, 0), (1, 0)
    assert calculate_angle(a, b, c) == pytest.approx(0.0, abs=0.01)


def test_calculate_angle_degenerate_zero_length():
    # B coincides with A -> undefined geometrically; must not crash or return NaN
    a, b, c = (0, 0), (0, 0), (1, 0)
    result = calculate_angle(a, b, c)
    assert result == 0.0


# ---------- Synthetic walker: known cadence, known stride time ----------

def _make_synthetic_walker(
    fps: float = 30.0,
    duration_s: float = 6.0,
    stride_period_s: float = 1.2,
    ankle_amplitude: float = 0.08,
    hip_velocity: float = 0.03,
) -> list[GaitFrame]:
    """Builds a simplified two-legged walker: hip moves at constant
    velocity, each ankle oscillates horizontally relative to the hip
    (driving gait-event detection), knee sits directly below the hip
    (driving a knee-flexion signal derived purely from ankle position).
    Not biomechanically realistic gait — deliberately simple so the
    ground truth (stride period, cadence) is known exactly."""
    n_frames = int(duration_s * fps)
    frames = []

    thigh_len, shank_len = 0.15, 0.15
    hip_y, shoulder_y_offset = 0.5, -0.25

    for i in range(n_frames):
        t = i / fps
        hip_x = 0.2 + hip_velocity * t

        landmarks = {}
        landmarks["left_shoulder"] = Landmark(x=hip_x, y=hip_y + shoulder_y_offset, visibility=1.0)
        landmarks["right_shoulder"] = Landmark(x=hip_x, y=hip_y + shoulder_y_offset, visibility=1.0)

        for side, phase in (("left", 0.0), ("right", math.pi)):  # contralateral: half-cycle offset
            ankle_rel_x = ankle_amplitude * math.sin(2 * math.pi * t / stride_period_s + phase)
            landmarks[f"{side}_hip"] = Landmark(x=hip_x, y=hip_y, visibility=1.0)
            landmarks[f"{side}_knee"] = Landmark(x=hip_x, y=hip_y + thigh_len, visibility=1.0)
            landmarks[f"{side}_ankle"] = Landmark(x=hip_x + ankle_rel_x, y=hip_y + thigh_len + shank_len, visibility=1.0)
            landmarks[f"{side}_heel"] = landmarks[f"{side}_ankle"]
            landmarks[f"{side}_toe"] = Landmark(
                x=hip_x + ankle_rel_x + 0.03, y=hip_y + thigh_len + shank_len, visibility=1.0
            )

        frames.append(GaitFrame(frame_index=i, timestamp_s=t, landmarks=landmarks))

    return frames


def test_event_detection_finds_correct_stride_period():
    fps = 30.0
    stride_period_s = 1.2
    frames = _make_synthetic_walker(fps=fps, stride_period_s=stride_period_s, duration_s=8.0)

    events = detect_gait_events(frames, Side.left, fps)

    assert len(events.initial_contacts) >= 4, "should detect multiple strides in an 8s clip"

    stride_intervals_s = [
        (b - a) / fps for a, b in zip(events.initial_contacts, events.initial_contacts[1:])
    ]
    avg_stride = sum(stride_intervals_s) / len(stride_intervals_s)

    # within 10% of the known synthetic stride period
    assert avg_stride == pytest.approx(stride_period_s, rel=0.1)


def test_cadence_matches_known_synthetic_rate():
    fps = 30.0
    stride_period_s = 1.2
    duration_s = 8.0
    frames = _make_synthetic_walker(fps=fps, stride_period_s=stride_period_s, duration_s=duration_s)

    events_by_side = {
        Side.left: detect_gait_events(frames, Side.left, fps),
        Side.right: detect_gait_events(frames, Side.right, fps),
    }
    metrics = compute_gait_metrics(events_by_side, {}, fps, duration_s)

    # Two feet, each stepping once per stride_period_s -> expected cadence:
    expected_cadence = 2 * (60.0 / stride_period_s)
    assert metrics.cadence_steps_per_min == pytest.approx(expected_cadence, rel=0.15)


def test_gait_cycles_segment_between_consecutive_ics():
    fps = 30.0
    frames = _make_synthetic_walker(fps=fps, duration_s=6.0)
    events = detect_gait_events(frames, Side.left, fps)
    cycles = build_gait_cycles(frames, events, fps)

    assert len(cycles) == len(events.initial_contacts) - 1
    for cycle, (start, end) in zip(cycles, zip(events.initial_contacts, events.initial_contacts[1:])):
        assert cycle.start_frame == start
        assert cycle.end_frame == end


# ---------- Angle series / ROM ----------

def test_raw_angle_series_and_rom_from_synthetic_walker():
    fps = 30.0
    frames = _make_synthetic_walker(fps=fps, duration_s=6.0, ankle_amplitude=0.08)

    raw = compute_raw_angle_series(frames, "knee", Side.left)
    assert len(raw.angle_degrees) == len(frames)

    # Straight leg (ankle directly below knee) should read close to 0 degrees;
    # the synthetic walker's ankle passes through that point every half-cycle.
    assert min(raw.angle_degrees) < 5.0

    # ROM should be positive and bounded (not some absurd/degenerate value)
    rom = max(raw.angle_degrees) - min(raw.angle_degrees)
    assert 0 < rom < 90


def test_resample_to_percent_cycle_endpoints():
    frames = _make_synthetic_walker(fps=30.0, duration_s=2.0)
    raw = compute_raw_angle_series(frames, "knee", Side.left)
    resampled = resample_to_percent_cycle(raw, num_points=101)

    assert resampled.percent_gait_cycle[0] == pytest.approx(0.0)
    assert resampled.percent_gait_cycle[-1] == pytest.approx(100.0)
    assert len(resampled.angle_degrees) == 101
    # resampled endpoints should match the raw series' first/last values
    assert resampled.angle_degrees[0] == pytest.approx(raw.angle_degrees[0], abs=0.5)
    assert resampled.angle_degrees[-1] == pytest.approx(raw.angle_degrees[-1], abs=0.5)


def test_missing_landmarks_are_skipped_not_fabricated():
    frames = [
        GaitFrame(frame_index=0, timestamp_s=0.0, landmarks={}),  # no landmarks at all
        GaitFrame(
            frame_index=1,
            timestamp_s=0.033,
            landmarks={
                "left_hip": Landmark(x=0.5, y=0.5, visibility=1.0),
                "left_knee": Landmark(x=0.5, y=0.65, visibility=1.0),
                "left_ankle": Landmark(x=0.5, y=0.8, visibility=1.0),
            },
        ),
    ]
    raw = compute_raw_angle_series(frames, "knee", Side.left)
    assert len(raw.angle_degrees) == 1  # only the frame with all 3 landmarks counts
    assert raw.frame_indices == [1]
