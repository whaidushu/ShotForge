from __future__ import annotations

from typing import Any

from shotforge.core.project_state import OutputLanguage
from shotforge.i18n import get_translator


LEGACY_KEY_MAP = {
    "audience": "design.audience",
    "mood_moody": "design.mood.moody",
    "mood_energetic": "design.mood.energetic",
    "constraints": "design.constraints",
    "titles": "design.titles",
    "shot_types": "design.shot_types",
    "description": "design.description",
    "key_visuals": "design.key_visuals",
    "cameras": "design.cameras",
    "transitions": "design.transitions",
    "subject_motion": "design.subject_motion",
    "pacing_hook": "design.pacing.hook",
    "pacing_escalation": "design.pacing.escalation",
    "music": "design.music",
    "sound_design": "design.sound_design",
    "prompt_visual_style": "design.prompt.visual_style",
    "prompt_key_visuals": "design.prompt.key_visuals",
    "prompt_audio_intent": "design.prompt.audio_intent",
    "csv_headers": "exports.csv_headers",
    "md": "exports.markdown",
}


def t(language: OutputLanguage, key: str) -> Any:
    return get_translator().t(language, LEGACY_KEY_MAP.get(key, key))
