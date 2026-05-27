from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import AudioCue, ProjectState
from shotforge.core.trace_log import TraceLog
from shotforge.l10n import t


def audio_cue_agent(state: ProjectState, context_builder: ContextBuilder) -> ProjectState:
    with TraceLog(state).span("audio_cue_agent"):
        context_builder.build(state, "Audio Cue Agent", ["audio", "sound-design"])
        state.audio_cues = [
            AudioCue(
                shot_id=shot.shot_id,
                music=t(state.language, "music"),
                sound_design=t(state.language, "sound_design"),
                voiceover=None,
            )
            for shot in state.shots
        ]
    return state
