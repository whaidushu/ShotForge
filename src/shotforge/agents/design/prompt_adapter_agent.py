from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.physical_targets import physical_contract_text, required_element_labels
from shotforge.core.project_state import (
    runtime_language,
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
        physical_targets = state.metadata.get("physical_targets") or {}
        target_contract = str(
            physical_targets.get("prompt_contract")
            or physical_contract_text(physical_targets.get("targets", []))
        )
        required_elements = required_element_labels(physical_targets)
        identity_constraints = [str(item) for item in physical_targets.get("identity_constraints", [])]
        spatial_relationships = [str(item) for item in physical_targets.get("spatial_relationships", [])]
        motion_contracts = [str(item) for item in physical_targets.get("motion_contracts", [])]
        semantic_negative_constraints = [
            str(item) for item in physical_targets.get("negative_constraints", [])
        ]
        semantic_success_criteria = [str(item) for item in physical_targets.get("success_criteria", [])]
        effect_contract = state.metadata.get("effect_contract") or {}
        contract_targets = _contract_targets(effect_contract)
        contract_lines = _contract_lines(contract_targets)
        contract_success_criteria = _contract_success_criteria(contract_targets)
        contract_negative_constraints = _contract_negative_constraints(contract_targets)
        for shot in state.shots:
            motion = shot.motion
            audio = next(item for item in state.audio_cues if item.shot_id == shot.shot_id)
            motion_text = f"{motion.camera}, {motion.subject_motion}" if motion else ""
            scene = next(item for item in state.scenes if item.scene_id == shot.scene_id)
            structured_template = StructuredPromptTemplate(
                character_identity=character_identity,
                scene_constraints=f"{scene.title}: {scene.description}",
                physical_constraints=[
                    *contract_lines,
                    target_contract,
                    f"MANDATORY VISIBLE ELEMENTS: {', '.join(required_elements)}.",
                    *identity_constraints,
                    *spatial_relationships,
                    *motion_contracts,
                    "Keep the exact requested subject count; do not duplicate or drop primary subjects.",
                    "Preserve named colors, materials, props, and scene anchors.",
                    f"Required visible elements: {', '.join(shot.key_visuals)}",
                ],
                action_sequence=shot.description,
                emotional_direction=scene.emotional_goal,
                camera_direction=shot.shot_type,
                motion_direction=motion_text,
                narrative_beat=f"{', '.join(shot.key_visuals)}. Audio: {audio.music}",
                style_constraints=f"{state.style}, {state.target_platform}, 16:9",
                success_criteria=[
                    *contract_success_criteria,
                    f"all mandatory physical targets are visible: {', '.join(required_elements)}",
                    *semantic_success_criteria,
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
                    prompt=_render_legacy_prompt(
                        state,
                        shot,
                        motion_text,
                        audio.music,
                        target_contract,
                        required_elements,
                    ),
                    structured_template=structured_template,
                    negative_prompt=", ".join(
                        [
                            _negative_prompt(required_elements),
                            *semantic_negative_constraints,
                            *contract_negative_constraints,
                        ]
                    ),
                    parameters={
                        "duration_seconds": shot.duration_seconds,
                        "aspect_ratio": "16:9",
                        "motion_strength": 0.68,
                        "seed_policy": "fixed-per-shot",
                        "effect_contract_id": effect_contract.get("contract_id", ""),
                        "effect_target_count": len(contract_targets),
                    },
                )
            )
        state.prompt_package = PromptPackage(
            provider="local-test-video-provider",
            prompts=prompts,
            adapter_notes=["V0 structured prompt package", "Effect contract injected during prompt adaptation"],
            metadata={
                "effect_contract_id": effect_contract.get("contract_id", ""),
                "effect_contract_stage": state.metadata.get("effect_contract_stage", ""),
            },
        )
    return state


def _render_legacy_prompt(
    state: ProjectState,
    shot,
    motion_text: str,
    audio_music: str,
    target_contract: str,
    required_elements: list[str],
) -> str:
    return (
        f"{_legacy_effect_contract_text(state)} "
        f"{target_contract} "
        f"MANDATORY VISIBLE ELEMENTS: {', '.join(required_elements)}. "
        f"{shot.description}. {shot.shot_type}, {motion_text}. "
        f"{t(runtime_language(state), 'prompt_visual_style')}: {state.style}. "
        f"{t(runtime_language(state), 'prompt_key_visuals')}: "
        f"{', '.join(shot.key_visuals)}. "
        f"{t(runtime_language(state), 'prompt_audio_intent')}: {audio_music}."
    )


def _negative_prompt(required_elements: list[str]) -> str:
    missing_terms = [
        f"missing {element}"
        for element in required_elements
    ]
    return ", ".join(
        [
            "low quality",
            "distorted anatomy",
            "unreadable text",
            "flicker",
            "missing primary subject",
            "missing required object",
            "missing location",
            "object morphing",
            "action morphing",
            "attribute detached from target",
            *missing_terms,
        ]
    )


def _contract_targets(effect_contract: dict) -> list[dict]:
    targets = effect_contract.get("targets", []) if isinstance(effect_contract, dict) else []
    return [target for target in targets if isinstance(target, dict)]


def _contract_lines(contract_targets: list[dict]) -> list[str]:
    lines = []
    for target in contract_targets[:16]:
        target_id = str(target.get("target_id", ""))
        label = str(target.get("label", ""))
        target_type = str(target.get("target_type", ""))
        evidence_rule = str(target.get("evidence_rule", ""))
        threshold = target.get("threshold", "")
        if not label:
            continue
        lines.append(
            "EFFECT CONTRACT "
            f"[{target_id}]: {label}; type={target_type}; threshold={threshold}; evidence={evidence_rule}"
        )
    return lines


def _contract_success_criteria(contract_targets: list[dict]) -> list[str]:
    criteria = []
    for target in contract_targets[:16]:
        label = str(target.get("label", ""))
        evidence_rule = str(target.get("evidence_rule", ""))
        if label:
            criteria.append(f"target {label} passes: {evidence_rule}")
    return criteria


def _contract_negative_constraints(contract_targets: list[dict]) -> list[str]:
    values = []
    for target in contract_targets:
        values.extend(str(item) for item in target.get("negative_hints", []) if str(item).strip())
        if target.get("target_type") == "negative_constraint" and target.get("label"):
            values.append(str(target["label"]))
    return values


def _legacy_effect_contract_text(state: ProjectState) -> str:
    effect_contract = state.metadata.get("effect_contract") or {}
    targets = _contract_targets(effect_contract)
    if not targets:
        return "EFFECT CONTRACT: no explicit hard targets extracted."
    compact_targets = [
        f"{target.get('target_id')}={target.get('label')}"
        for target in targets[:10]
        if target.get("label")
    ]
    return "EFFECT CONTRACT: " + "; ".join(compact_targets) + "."
