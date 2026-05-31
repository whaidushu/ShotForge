from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.physical_targets import extract_physical_targets
from shotforge.core.project_state import CharacterSpec, CreativeIntent, ProjectState
from shotforge.core.trace_log import TraceLog
from shotforge.l10n import t
from shotforge.skills import SkillRegistry


def intent_agent(
    state: ProjectState,
    context_builder: ContextBuilder,
    registry: SkillRegistry,
) -> ProjectState:
    with TraceLog(state).span("intent_agent"):
        context = context_builder.build(state, "Intent Agent", ["cinematic", "visual"])
        tool_name = _llm_tool_name()
        completion = registry.call(
            tool_name,
            context.as_prompt(),
            purpose="intent",
            agent_name="intent_agent",
            expected_output="creative intent draft",
            fallback_tools=["mock_llm.complete"] if tool_name != "mock_llm.complete" else [],
        )
        lower_idea = state.user_idea.lower()
        genre = "sci-fi" if any(term in lower_idea for term in ["ai", "cyber", "赛博"]) else state.style
        mood_key = (
            "mood_moody"
            if any(term in lower_idea for term in ["rain", "雨", "night", "夜"])
            else "mood_energetic"
        )
        physical_targets = extract_physical_targets(state.user_idea, state.language)
        state.metadata["physical_targets"] = physical_targets
        primary_subject = next(
            (
                target
                for target in physical_targets["targets"]
                if target.get("type") == "subject"
            ),
            None,
        )
        state.creative_intent = CreativeIntent(
            premise=state.user_idea,
            genre=genre,
            audience=t(state.language, "audience"),
            mood=t(state.language, mood_key),
            visual_style=state.style,
            constraints=[
                *t(state.language, "constraints"),
                physical_targets["prompt_contract"],
                "Every required physical target must be visible or the generation should be treated as failed.",
                completion,
            ],
        )
        state.characters = [
            CharacterSpec(
                character_id="char_primary",
                name="主角" if state.language == "zh" else "Primary Subject",
                role="视觉叙事核心" if state.language == "zh" else "visual narrative focus",
                visual_traits=[
                    state.style,
                    "clear silhouette",
                    *(primary_subject.get("aliases", []) if primary_subject else []),
                ],
                behavior_notes=["movement must stay readable"],
            )
        ]
    return state


def _llm_tool_name() -> str:
    from shotforge.config import get_settings

    return "mock_llm.complete" if get_settings().llm_provider == "mock" else "llm.complete"
