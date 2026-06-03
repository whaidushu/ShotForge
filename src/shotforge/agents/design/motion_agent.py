from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import MotionSpec, ProjectState, runtime_language
from shotforge.core.trace_log import TraceLog
from shotforge.l10n import t


def motion_agent(state: ProjectState, context_builder: ContextBuilder) -> ProjectState:
    with TraceLog(state).span("motion_agent"):
        context_builder.build(state, "Motion Agent", ["motion", "pacing"])
        cameras = t(runtime_language(state), "cameras")
        transitions = t(runtime_language(state), "transitions")
        for shot in state.shots:
            beat = shot.metadata.get("story_beat", {})
            shot.motion = MotionSpec(
                shot_id=shot.shot_id,
                camera=str(beat.get("camera") or cameras[(shot.index - 1) % len(cameras)]),
                subject_motion=str(beat.get("subject_motion") or t(runtime_language(state), "subject_motion")),
                transition=str(
                    beat.get("transition") or transitions[(shot.index - 1) % len(transitions)]
                ),
                pacing=str(
                    beat.get("pacing")
                    or (
                        t(runtime_language(state), "pacing_hook")
                        if shot.index == 1
                        else t(runtime_language(state), "pacing_escalation")
                    )
                ),
            )
    return state
