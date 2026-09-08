"""
Segments a side's initial-contact events into gait cycles: IC to next
IC, 0-100% normalized. This is the piece that turns a list of events
into the `GaitCycle` objects the internal data contract expects.
"""
from app.gait.events import GaitEvents
from app.pipeline.gait_types import GaitCycle, GaitFrame, Side


def build_gait_cycles(frames: list[GaitFrame], events: GaitEvents, fps: float) -> list[GaitCycle]:
    cycles: list[GaitCycle] = []
    ics = events.initial_contacts

    if len(ics) < 2 or fps <= 0:
        return cycles

    frame_by_index = {f.frame_index: f for f in frames}

    for start_frame, end_frame in zip(ics, ics[1:]):
        start_t = frame_by_index[start_frame].timestamp_s if start_frame in frame_by_index else start_frame / fps
        end_t = frame_by_index[end_frame].timestamp_s if end_frame in frame_by_index else end_frame / fps

        cycles.append(
            GaitCycle(
                side=events.side,
                start_frame=start_frame,
                end_frame=end_frame,
                start_time_s=start_t,
                end_time_s=end_t,
                percent_normalized_frame_indices=list(range(start_frame, end_frame + 1)),
            )
        )

    return cycles
