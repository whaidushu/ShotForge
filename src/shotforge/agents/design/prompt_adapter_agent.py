from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import (
    ProjectState,
    PromptItem,
    PromptPackage,
    StructuredPromptTemplate,
)
from shotforge.core.trace_log import TraceLog
from shotforge.l10n import t


def prompt_adapter_agent(state: ProjectState, context_builder: ContextBuilder) -> ProjectState:
    with TraceLog(state).span("prompt_adapter_agent"):
        context_builder.build(state, "Prompt Adapter Agent", ["prompt", "video-model"])
        prompts: list[PromptItem] = []
        character_identity = "; ".join(
            [
                f"{character.name}: {character.role}, {', '.join(character.visual_traits)}"
                for character in state.characters
            ]
        )
        for shot in state.shots:
            motion = shot.motion
            audio = next(item for item in state.audio_cues if item.shot_id == shot.shot_id)
            motion_text = f"{motion.camera}, {motion.subject_motion}" if motion else ""
            scene = next(item for item in state.scenes if item.scene_id == shot.scene_id)
            structured_template = StructuredPromptTemplate(
                character_identity=character_identity,
                scene_constraints=f"{scene.title}: {scene.description}",
                action_sequence=shot.description,
                emotional_direction=scene.emotional_goal,
                camera_direction=shot.shot_type,
                motion_direction=motion_text,
                narrative_beat=f"{', '.join(shot.key_visuals)}. Audio: {audio.music}",
                style_constraints=f"{state.style}, {state.target_platform}, 16:9",
                success_criteria=[
                    "primary subject is visible",
                    "main action is readable",
                    "camera, motion, and audio cues align with the beat",
                ],
                comfyui_params={
                    "duration_seconds": shot.duration_seconds,
                    "aspect_ratio": "16:9",
                    "seed_policy": "fixed-per-shot",
                },
                metadata={"schema_version": "structured_prompt_v1"},
            )
            prompts.append(
                PromptItem(
                    shot_id=shot.shot_id,
                    prompt=_render_legacy_prompt(state, shot, motion_text, audio.music),
                    structured_template=structured_template,
                    parameters={
                        "duration_seconds": shot.duration_seconds,
                        "aspect_ratio": "16:9",
                        "motion_strength": 0.68,
                        "seed_policy": "fixed-per-shot",
                    },
                )
            )
        state.prompt_package = PromptPackage(
            provider="mock-video-model",
            prompts=prompts,
            adapter_notes=["V0 design harness prompt package"],
        )
    return state


def _render_legacy_prompt(state: ProjectState, shot, motion_text: str, audio_music: str) -> str:
    return (
        f"{shot.description}. {shot.shot_type}, {motion_text}. "
        f"{t(state.language, 'prompt_visual_style')}: {state.style}. "
        f"{t(state.language, 'prompt_key_visuals')}: "
        f"{', '.join(shot.key_visuals)}. "
        f"{t(state.language, 'prompt_audio_intent')}: {audio_music}."
    )
