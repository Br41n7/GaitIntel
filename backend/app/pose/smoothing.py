"""
Landmark smoothing and missing-landmark handling.

MediaPipe's per-frame pose estimates jitter, and visibility drops
during occlusion (e.g. one leg passing behind the other). Both would
otherwise corrupt downstream angle/metric calculations, so this runs
right at the pose-extraction boundary — nothing past this point should
have to deal with raw jitter or missing points.

Approach (deliberately simple for v0.1 — revisit only if real footage
shows it's not enough):
- Exponential moving average per landmark coordinate, across frames.
- Below VISIBILITY_THRESHOLD, treat the point as missing and hold the
  last smoothed value instead of trusting the noisy new one.
"""
from app.pipeline.gait_types import GaitFrame, Landmark

VISIBILITY_THRESHOLD = 0.5
EMA_ALPHA = 0.5  # higher = trusts new frames more, lower = smoother/laggier


def smooth_frames(frames: list[GaitFrame]) -> list[GaitFrame]:
    if not frames:
        return frames

    smoothed_state: dict[str, Landmark] = {}
    smoothed_frames: list[GaitFrame] = []

    for frame in frames:
        new_landmarks: dict[str, Landmark] = {}

        for name, lm in frame.landmarks.items():
            is_visible = lm.visibility is None or lm.visibility >= VISIBILITY_THRESHOLD
            prev = smoothed_state.get(name)

            if not is_visible and prev is not None:
                # Missing-landmark handling: hold last known good value
                # rather than propagating a noisy/occluded estimate.
                new_landmarks[name] = prev
                continue

            if prev is None:
                smoothed = lm
            else:
                smoothed = Landmark(
                    x=EMA_ALPHA * lm.x + (1 - EMA_ALPHA) * prev.x,
                    y=EMA_ALPHA * lm.y + (1 - EMA_ALPHA) * prev.y,
                    z=(EMA_ALPHA * lm.z + (1 - EMA_ALPHA) * prev.z)
                    if lm.z is not None and prev.z is not None
                    else lm.z,
                    visibility=lm.visibility,
                )

            smoothed_state[name] = smoothed
            new_landmarks[name] = smoothed

        smoothed_frames.append(
            GaitFrame(
                frame_index=frame.frame_index,
                timestamp_s=frame.timestamp_s,
                landmarks=new_landmarks,
            )
        )

    return smoothed_frames
