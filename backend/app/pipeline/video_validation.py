"""
Basic video validation before it enters the pipeline. Deliberately
cheap checks — this is not trying to assess video quality, just catch
obviously broken uploads before they waste a pose-extraction pass.
"""
import os

from app.core.config import settings
from app.pose.mediapipe_provider import read_video_metadata

MIN_DURATION_S = 1.0
MIN_FRAMES = 10


class VideoValidationError(ValueError):
    pass


def validate_video(video_path: str) -> None:
    if not os.path.exists(video_path):
        raise VideoValidationError(f"Video file not found: {video_path}")

    if os.path.getsize(video_path) == 0:
        raise VideoValidationError("Video file is empty")

    try:
        metadata = read_video_metadata(video_path)
    except Exception as e:
        raise VideoValidationError(f"Could not read video: {e}") from e

    if metadata.frame_count < MIN_FRAMES:
        raise VideoValidationError(
            f"Video has too few frames ({metadata.frame_count}); need at least {MIN_FRAMES}"
        )

    if metadata.duration_s < MIN_DURATION_S:
        raise VideoValidationError(
            f"Video is too short ({metadata.duration_s:.2f}s); need at least {MIN_DURATION_S}s"
        )

    if metadata.frame_count > settings.max_pose_extraction_frames:
        raise VideoValidationError(
            f"Video has {metadata.frame_count} frames, which exceeds the "
            f"{settings.max_pose_extraction_frames}-frame limit for this deployment. "
            "This limit exists to avoid running out of memory or timing out on "
            "constrained hosting (e.g. Render's free tier) — trim the clip shorter "
            "or raise MAX_POSE_EXTRACTION_FRAMES if running on hardware that can handle it."
        )
