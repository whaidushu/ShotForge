from __future__ import annotations

import math

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.physical_targets import required_element_labels
from shotforge.core.project_state import ProjectState, SceneSpec, ShotSpec
from shotforge.core.trace_log import TraceLog
from shotforge.l10n import t


def storyboard_agent(state: ProjectState, context_builder: ContextBuilder) -> ProjectState:
    with TraceLog(state).span("storyboard_agent"):
        context_builder.build(state, "Storyboard Agent", ["short-form", "pacing"])
        scene_count = 4 if state.duration_seconds <= 30 else 6
        base_duration = max(3, math.floor(state.duration_seconds / scene_count))
        titles = t(state.language, "titles")
        shot_types = t(state.language, "shot_types")
        scenes: list[SceneSpec] = []
        shots: list[ShotSpec] = []
        required_elements = required_element_labels(state.metadata.get("physical_targets"))

        for index in range(1, scene_count + 1):
            duration = base_duration
            if index == scene_count:
                duration = state.duration_seconds - base_duration * (scene_count - 1)
            title = titles[index - 1]
            scene_id = f"scene_{index:02d}"
            description = t(state.language, "description").format(title=title, idea=state.user_idea)
            key_visuals = [
                state.creative_intent.visual_style if state.creative_intent else state.style,
                *required_elements,
                *t(state.language, "key_visuals"),
            ]
            scenes.append(
                SceneSpec(
                    scene_id=scene_id,
                    index=index,
                    title=title,
                    duration_seconds=duration,
                    description=description,
                    emotional_goal=state.creative_intent.mood if state.creative_intent else "dynamic",
                    key_visuals=key_visuals,
                )
            )
            shots.append(
                ShotSpec(
                    shot_id=f"shot_{index:02d}",
                    scene_id=scene_id,
                    index=index,
                    title=title,
                    duration_seconds=duration,
                    description=description,
                    shot_type=shot_types[(index - 1) % len(shot_types)],
                    key_visuals=key_visuals,
                )
            )

        state.scenes = scenes
        state.shots = shots
    return state
