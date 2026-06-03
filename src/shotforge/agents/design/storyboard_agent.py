from __future__ import annotations

import math

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.physical_targets import required_element_labels
from shotforge.core.project_state import ProjectState, SceneSpec, ShotSpec, runtime_language
from shotforge.core.trace_log import TraceLog
from shotforge.agents.design.story_blueprint import build_story_beats
from shotforge.l10n import t


def storyboard_agent(state: ProjectState, context_builder: ContextBuilder) -> ProjectState:
    with TraceLog(state).span("storyboard_agent"):
        context_builder.build(state, "Storyboard Agent", ["short-form", "pacing"])
        scene_count = 4 if state.duration_seconds <= 30 else 6
        base_duration = max(3, math.floor(state.duration_seconds / scene_count))
        titles = t(runtime_language(state), "titles")
        shot_types = t(runtime_language(state), "shot_types")
        scenes: list[SceneSpec] = []
        shots: list[ShotSpec] = []
        required_elements = required_element_labels(state.metadata.get("physical_targets"))
        story_beats = build_story_beats(
            idea=state.user_idea,
            language=runtime_language(state),
            required_elements=required_elements,
            count=scene_count,
        )

        for index in range(1, scene_count + 1):
            beat = story_beats[index - 1]
            duration = base_duration
            if index == scene_count:
                duration = state.duration_seconds - base_duration * (scene_count - 1)
            title = titles[index - 1]
            scene_id = f"scene_{index:02d}"
            description = beat.description
            key_visuals = [
                state.creative_intent.visual_style if state.creative_intent else state.style,
                *required_elements,
                *beat.key_visuals,
                *t(runtime_language(state), "key_visuals"),
            ]
            scenes.append(
                SceneSpec(
                    scene_id=scene_id,
                    index=index,
                    title=title,
                    duration_seconds=duration,
                    description=description,
                    emotional_goal=beat.emotional_goal,
                    key_visuals=key_visuals,
                    metadata={"story_beat": beat.__dict__},
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
                    shot_type=beat.shot_type or shot_types[(index - 1) % len(shot_types)],
                    key_visuals=key_visuals,
                    metadata={"story_beat": beat.__dict__},
                )
            )

        state.scenes = scenes
        state.shots = shots
    return state
