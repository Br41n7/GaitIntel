"""
Maps MediaPipe's 33-point pose model onto the named joints this
project actually needs (hip, knee, ankle, heel, toe, per side). This
is the ONLY file that should know MediaPipe's landmark indices — if a
future provider (RTMPose, MyoGait) uses different indices, only its
own module needs this kind of mapping, not any shared code.
"""

# MediaPipe Pose landmark indices (BlazePose 33-point model).
# Reference: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
MEDIAPIPE_LANDMARK_MAP: dict[str, int] = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_toe": 31,  # MediaPipe calls this "foot_index"
    "right_toe": 32,
}

# The subset we actually use for sagittal-plane gait analysis. Shoulders
# are kept for trunk-lean detection later (deviation #8) but aren't part
# of the "hip/knee/ankle/heel/toe" acceptance-test requirement.
GAIT_RELEVANT_LANDMARKS = list(MEDIAPIPE_LANDMARK_MAP.keys())
