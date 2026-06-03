from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import AudioCue, ProjectState, runtime_language
from shotforge.core.trace_log import TraceLog
from shotforge.l10n import t


def audio_cue_agent(state: ProjectState, context_builder: ContextBuilder) -> ProjectState:
    with TraceLog(state).span("audio_cue_agent"):
        context_builder.build(state, "Audio Cue Agent", ["audio", "sound-design"])
        state.audio_cues = [
            AudioCue(
                shot_id=shot.shot_id,
                music=str(shot.metadata.get("story_beat", {}).get("music") or t(runtime_language(state), "music")),
                sound_design=list(
                    shot.metadata.get("story_beat", {}).get("sound_design")
                    or t(runtime_language(state), "sound_design")
                ),
                voiceover=None,
            )
            for shot in state.shots
        ]
    return state
