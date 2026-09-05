"""
PoseProvider interface. This is the seam that lets you start with
MediaPipe and later swap in MyoGait, RTMPose, or anything else without
touching gait math, deviation detection, or the frontend.

Implement `MediaPipePoseProvider` in Phase 2 of the build order. Until
then, anything importing this can rely on the interface existing even
though there's no concrete implementation yet.
"""
from abc import ABC, abstractmethod

from app.pipeline.gait_types import GaitFrame


class PoseProvider(ABC):
    @abstractmethod
    def extract(self, video_path: str) -> list[GaitFrame]:
        """Run pose estimation on a video and return one GaitFrame per
        processed frame, already converted into the internal Landmark
        format. Implementations own all vendor-specific logic
        (landmark smoothing, missing-landmark handling, left/right
        identification) — nothing vendor-specific should escape this
        method."""
        raise NotImplementedError
