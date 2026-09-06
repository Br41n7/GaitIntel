"""
MediaPipePoseProvider: the first concrete PoseProvider implementation.

Owns everything MediaPipe-specific: reading the video, running the
pose model frame by frame, and converting MediaPipe's output into our
internal GaitFrame/Landmark format. Nothing outside this file should
ever import `mediapipe` directly — that's the whole point of the
adapter pattern (see app/pose/base.py).
"""
import logging

import cv2

from app.pipeline.gait_types import GaitFrame, Landmark
from app.pose.base import PoseProvider
from app.pose.landmarks import MEDIAPIPE_LANDMARK_MAP
from app.pose.smoothing import smooth_frames

logger = logging.getLogger(__name__)


class VideoMetadata:
    def __init__(self, fps: float, frame_count: int, width: int, height: int, duration_s: float):
        self.fps = fps
        self.frame_count = frame_count
        self.width = width
        self.height = height
        self.duration_s = duration_s


def read_video_metadata(video_path: str) -> VideoMetadata:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_s = (frame_count / fps) if fps else 0.0
        return VideoMetadata(fps=fps, frame_count=frame_count, width=width, height=height, duration_s=duration_s)
    finally:
        cap.release()


class MediaPipePoseProvider(PoseProvider):
    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

    def extract(self, video_path: str) -> list[GaitFrame]:
        # Imported lazily so the rest of the app (and tests that don't
        # need real pose extraction) doesn't pay MediaPipe's import
        # cost or require it to be installed.
        import mediapipe as mp

        metadata = read_video_metadata(video_path)
        if metadata.frame_count == 0:
            raise ValueError(f"Video has no readable frames: {video_path}")

        mp_pose = mp.solutions.pose
        raw_frames: list[GaitFrame] = []

        cap = cv2.VideoCapture(video_path)
        try:
            with mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            ) as pose:
                frame_index = 0
                while True:
                    success, frame_bgr = cap.read()
                    if not success:
                        break

                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    result = pose.process(frame_rgb)

                    landmarks: dict[str, Landmark] = {}
                    if result.pose_landmarks:
                        for name, idx in MEDIAPIPE_LANDMARK_MAP.items():
                            lm = result.pose_landmarks.landmark[idx]
                            landmarks[name] = Landmark(
                                x=lm.x,  # normalized 0-1, left-to-right
                                y=lm.y,  # normalized 0-1, top-to-bottom
                                z=lm.z,
                                visibility=lm.visibility,
                            )
                    else:
                        logger.warning("No pose detected in frame %d of %s", frame_index, video_path)

                    timestamp_s = frame_index / metadata.fps if metadata.fps else 0.0
                    raw_frames.append(
                        GaitFrame(frame_index=frame_index, timestamp_s=timestamp_s, landmarks=landmarks)
                    )
                    frame_index += 1
        finally:
            cap.release()

        if not raw_frames:
            raise ValueError(f"No frames could be processed from: {video_path}")

        return smooth_frames(raw_frames)
