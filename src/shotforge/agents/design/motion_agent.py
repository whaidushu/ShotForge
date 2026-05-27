from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import MotionSpec, ProjectState
from shotforge.core.trace_log import TraceLog
from shotforge.l10n import t


def motion_agent(state: ProjectState, context_builder: ContextBuilder) -> ProjectState:
    with TraceLog(state).span("motion_agent"):
        context_builder.build(state, "Motion Agent", ["motion", "pacing"])
        cameras = t(state.language, "cameras")
        transitions = t(state.language, "transitions")
        for shot in state.shots:
            shot.motion = MotionSpec(
                shot_id=shot.shot_id,
                camera=cameras[(shot.index - 1) % len(cameras)],
                subject_motion=t(state.language, "subject_motion"),
                transition=transitions[(shot.index - 1) % len(transitions)],
                pacing=(
                    t(state.language, "pacing_hook")
                    if shot.index == 1
                    else t(state.language, "pacing_escalation")
                ),
            )
    return state
