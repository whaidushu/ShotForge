from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from shotforge.config import get_settings
from shotforge.core.physical_convergence import (
    build_revision_plan_from_target_evaluation,
    compare_iteration_evaluations,
)
from shotforge.core.project_state import (
    AudioCue,
    FieldChange,
    MotionSpec,
    PromptItem,
    PromptPackage,
    ProjectState,
    SceneSpec,
    ShotSpec,
    StructuredPromptTemplate,
    VersionDiff,
    set_runtime_language,
)
from shotforge.exporters import ExportManager
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.evaluation_workflow import observe_generation, run_generation


DEFAULT_CASE_ID = "cyber_cat_rooftop"


def effect_case_root() -> Path:
    return Path(__file__).resolve().parents[3] / "examples" / "effect_cases"


def list_effect_cases() -> list[dict[str, Any]]:
    cases = []
    for path in sorted(effect_case_root().glob("*/acceptance_targets.json")):
        case = _load_case(path.parent.name)
        cases.append(
            {
                "case_id": case["case_id"],
                "title": case["title"],
                "duration_seconds": case["duration_seconds"],
                "path": str(path.parent),
            }
        )
    return cases


def run_effect_demo(
    case_id: str = DEFAULT_CASE_ID,
    *,
    language: str = "en",
    generator_provider_id: str = "mock",
    style: str | None = None,
) -> ProjectState:
    case = _load_case(case_id)
    idea = _case_idea(case, language)
    state = run_design_pipeline(
        idea=idea,
        style=style or case.get("style", "cinematic"),
        duration_seconds=max(12, int(case.get("duration_seconds", 5))),
        language="zh" if language == "zh" else "en",
    )
    set_runtime_language(state, "zh" if language == "zh" else "en")
    _prepare_single_shot_state(state, case)
    state.metadata["run_mode"] = "effect_demo"
    state.metadata["effect_demo_case_id"] = case["case_id"]
    state.metadata["effect_demo_targets"] = _targets_payload(case)
    state.metadata["physical_targets"] = _physical_targets_payload(case)

    v1_prompt = state.prompt_package.prompts[0].model_dump(mode="json")
    generated_v1 = run_generation(state, provider_id=generator_provider_id)
    _mark_generation_iteration(generated_v1, "v001")

    _apply_structured_prompt(state, case)
    v2_prompt = state.prompt_package.prompts[0].model_dump(mode="json")
    generated_v2 = run_generation(state, provider_id=generator_provider_id)
    _mark_generation_iteration(generated_v2, "v002")

    resource_events = [_release_generation_resources(generated_v2)]
    observe_generation(state, generated_v1)
    observe_generation(state, generated_v2)
    v1_evaluation = _evaluate_iteration(
        state=state,
        case=case,
        iteration="v1",
        prompt=PromptItem.model_validate(v1_prompt),
        generated_result_id=generated_v1.generated_result_id,
    )
    v2_evaluation = _evaluate_iteration(
        state=state,
        case=case,
        iteration="v2",
        prompt=state.prompt_package.prompts[0],
        generated_result_id=generated_v2.generated_result_id,
    )

    revision_plan = _build_revision_plan(case, v2_evaluation, target_iteration="v3")
    _apply_revision_plan(state, case, revision_plan, target_version=3)
    v3_prompt = state.prompt_package.prompts[0].model_dump(mode="json")
    generated_v3 = run_generation(state, provider_id=generator_provider_id)
    _mark_generation_iteration(generated_v3, "v003")
    resource_events.append(_release_generation_resources(generated_v3))
    observe_generation(state, generated_v3)
    v3_evaluation = _evaluate_iteration(
        state=state,
        case=case,
        iteration="v3",
        prompt=state.prompt_package.prompts[0],
        generated_result_id=generated_v3.generated_result_id,
    )

    comparison = _build_comparison(
        case,
        evaluations=[v1_evaluation, v2_evaluation, v3_evaluation],
        revision_plan=revision_plan,
        resource_events=resource_events,
    )
    effect_paths = _write_effect_outputs(
        state=state,
        case=case,
        v1_prompt=v1_prompt,
        v2_prompt=v2_prompt,
        v3_prompt=v3_prompt,
        evaluations=[v1_evaluation, v2_evaluation, v3_evaluation],
        revision_plan=revision_plan,
        comparison=comparison,
    )
    state.metadata["effect_demo"] = {
        "case_id": case["case_id"],
        "title": case["title"],
        "status": comparison["status"],
        "v1_score": comparison["v1_score"],
        "v2_score": comparison["v2_score"],
        "v3_score": comparison["v3_score"],
        "score_delta": comparison["score_delta"],
        "visual_observation_available": comparison["visual_observation_available"],
        "paths": effect_paths,
        "comparison": comparison,
        "revision_plan": revision_plan,
        "resource_events": resource_events,
    }
    ExportManager().export_all(state)
    return state


def load_effect_comparison(run_id: str) -> dict[str, Any]:
    comparison_dir = get_settings().runs_dir / run_id / "effect_demo" / "comparison"
    path = comparison_dir / "effect_convergence_report.json"
    if not path.exists():
        path = comparison_dir / "v1_v2_effect_report.json"
    if not path.exists():
        raise FileNotFoundError(f"Effect comparison not found for run: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_case(case_id: str) -> dict[str, Any]:
    path = effect_case_root() / case_id / "acceptance_targets.json"
    if not path.exists():
        raise FileNotFoundError(f"Effect case not found: {case_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _case_idea(case: dict[str, Any], language: str) -> str:
    ideas = case.get("language_ideas", {})
    return str(ideas.get(language) or ideas.get("en") or case["title"])


def _prepare_single_shot_state(state: ProjectState, case: dict[str, Any]) -> None:
    shot_payload = case["shot"]
    duration = int(case.get("duration_seconds", 5))
    scene = SceneSpec(
        scene_id="scene_01",
        index=1,
        title=shot_payload["title"],
        duration_seconds=duration,
        description=shot_payload["description"],
        emotional_goal="tense focused pursuit",
        key_visuals=list(case["required_elements"][:4]),
        metadata={"effect_case": case["case_id"]},
    )
    motion = MotionSpec(
        shot_id="shot_01",
        camera=shot_payload["camera"],
        subject_motion=shot_payload["motion"],
        transition="single continuous shot",
        pacing="fast but readable",
        metadata={"effect_case": case["case_id"]},
    )
    shot = ShotSpec(
        shot_id="shot_01",
        scene_id=scene.scene_id,
        index=1,
        title=shot_payload["title"],
        duration_seconds=duration,
        description=shot_payload["description"],
        shot_type=shot_payload["shot_type"],
        key_visuals=list(case["required_elements"]),
        motion=motion,
        metadata={"effect_case": case["case_id"]},
    )
    audio = AudioCue(
        shot_id=shot.shot_id,
        music=shot_payload["music"],
        sound_design=["rain ambience", "drone buzz", "wet rooftop footfalls"],
        metadata={"effect_case": case["case_id"]},
    )
    state.duration_seconds = duration
    state.scenes = [scene]
    state.shots = [shot]
    state.audio_cues = [audio]
    state.prompt_package = PromptPackage(
        provider="effect-demo",
        prompts=[_initial_prompt(case, shot, motion, audio)],
        adapter_notes=["Effect demo v1 intentionally keeps the first prompt compact."],
        metadata={"effect_case": case["case_id"], "iteration": "v1"},
    )
    state.touch()


def _initial_prompt(
    case: dict[str, Any],
    shot: ShotSpec,
    motion: MotionSpec,
    audio: AudioCue,
) -> PromptItem:
    prompt = _case_idea(case, "zh")
    return PromptItem(
        shot_id=shot.shot_id,
        provider="effect-demo",
        prompt=prompt,
        structured_template=None,
        negative_prompt="",
        parameters={
            "duration_seconds": shot.duration_seconds,
            "aspect_ratio": "16:9",
            "seed_policy": "fixed-per-shot",
            "effect_iteration": "v1",
            "effect_stage": "raw_user_prompt",
            "source_user_prompt": prompt,
            "translated_prompt": _case_idea(case, "en"),
            "audio": audio.music,
        },
    )


def _targets_payload(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "required_elements": case["required_elements"],
        "visual_attributes": case.get("visual_attributes", []),
        "spatial_relationships": case.get("spatial_relationships", []),
        "motion_contracts": case.get("motion_contracts", []),
        "negative_constraints": case.get("negative_constraints", []),
        "success_criteria": case.get("success_criteria", []),
    }


def _physical_targets_payload(case: dict[str, Any]) -> dict[str, Any]:
    targets = [
        {
            "target_id": f"effect_{_slug(element)}",
            "type": "subject" if index == 0 else "object",
            "label": element,
            "aliases": _aliases_for(element),
            "required": True,
            "visibility": "must_be_visible",
        }
        for index, element in enumerate(case["required_elements"])
    ]
    return {
        "source_text": _case_idea(case, "en"),
        "targets": targets,
        "required_elements": case["required_elements"],
        "prompt_contract": "; ".join(case.get("success_criteria", [])),
    }


def _evaluate_iteration(
    *,
    state: ProjectState,
    case: dict[str, Any],
    iteration: str,
    prompt: PromptItem,
    generated_result_id: str,
) -> dict[str, Any]:
    generated = next(item for item in state.generation_results if item.generated_result_id == generated_result_id)
    generated_shot = generated.shots[0]
    frame_texts = [
        _observation_text(frame.model_dump(mode="json"))
        for frame in generated_shot.frame_observations
    ]
    generated_text = " ".join(
        [
            generated_shot.observed_summary,
            " ".join(generated_shot.detected_elements),
            generated_shot.motion_summary,
        ]
    )
    prompt_text = " ".join(
        [
            prompt.prompt,
            prompt.structured_template.render() if prompt.structured_template else "",
            prompt.negative_prompt,
        ]
    )
    target_scores = []
    for element in case["required_elements"]:
        aliases = _aliases_for(element)
        frame_hits = [
            index
            for index, text in enumerate(frame_texts)
            if _contains_alias(text, aliases)
        ]
        generated_hit = _contains_alias(generated_text, aliases)
        prompt_hit = _contains_alias(prompt_text, aliases)
        contract_hit = _contains_alias(
            " ".join(case.get("success_criteria", []) + case.get("negative_constraints", [])),
            aliases,
        )
        if frame_texts:
            visual_score = len(frame_hits) / len(frame_texts)
        else:
            visual_score = 0.8 if generated_hit else 0.0
        prompt_score = 0.25
        if prompt_hit:
            prompt_score += 0.45
        if contract_hit and prompt_hit:
            prompt_score += 0.2
        if iteration in {"v2", "v3"} and prompt_hit:
            prompt_score += 0.1
        prompt_score = min(1.0, prompt_score)
        if frame_texts:
            score = round(0.7 * visual_score + 0.3 * prompt_score, 3)
        else:
            score = round(0.85 * prompt_score, 3)
        presence_ratio = len(frame_hits) / len(frame_texts) if frame_texts else visual_score
        if score >= 0.75 and (not frame_texts or presence_ratio >= 0.8):
            status = "passed"
        elif score >= 0.45:
            status = "weak"
        else:
            status = "failed"
        target_scores.append(
            {
                "target": element,
                "aliases": aliases,
                "score": score,
                "visual_score": round(visual_score, 3),
                "prompt_score": round(prompt_score, 3),
                "frame_hits": frame_hits,
                "sampled_frame_count": len(frame_texts),
                "generated_hit": generated_hit,
                "prompt_hit": prompt_hit,
                "status": status,
            }
        )
    issues = [
        {
            "target": item["target"],
            "type": "missing_or_weak_physical_target",
            "severity": "high" if item["score"] < 0.45 else "medium",
            "evidence": (
                f"frames={len(item['frame_hits'])}/{item['sampled_frame_count']}, "
                f"generated_hit={item['generated_hit']}, prompt_hit={item['prompt_hit']}"
            ),
        }
        for item in target_scores
        if item["status"] != "passed"
    ]
    return {
        "iteration": iteration,
        "generated_result_id": generated_result_id,
        "provider": generated.provider,
        "video_refs": generated.artifact_refs,
        "visual_observation_available": bool(frame_texts),
        "observer_id": generated.metadata.get("frame_observation_provider", ""),
        "sampled_frame_count": len(frame_texts),
        "overall_score": round(mean(item["score"] for item in target_scores), 3),
        "target_scores": target_scores,
        "issues": issues,
    }


def _apply_structured_prompt(state: ProjectState, case: dict[str, Any]) -> None:
    before_prompt = state.prompt_package.prompts[0].model_dump(mode="json")
    shot = state.shots[0]
    prompt = state.prompt_package.prompts[0]
    required = case["required_elements"]
    relationship_text = "; ".join(case.get("spatial_relationships", []) + case.get("motion_contracts", []))
    translated_prompt = _case_idea(case, "en")
    prompt.prompt = (
        f"{translated_prompt} "
        f"{case['shot']['description']} "
        f"Camera: {case['shot']['shot_type']}. "
        f"Motion: {case['shot']['motion']}. "
        f"Style: {case.get('style', state.style)}."
    )
    prompt.negative_prompt = "low quality, distorted anatomy, unreadable text, flicker"
    prompt.parameters["effect_iteration"] = "v2"
    prompt.parameters["effect_stage"] = "structured_translated_prompt"
    prompt.parameters["source_user_prompt"] = _case_idea(case, "zh")
    prompt.parameters["translated_prompt"] = translated_prompt
    prompt.structured_template = StructuredPromptTemplate(
        character_identity="cybernetic cat pursuing a glowing drone",
        scene_constraints=case["shot"]["description"],
        physical_constraints=[
            f"Visible elements requested by the user: {', '.join(required)}",
            *case.get("visual_attributes", []),
            *case.get("spatial_relationships", []),
        ],
        action_sequence=relationship_text,
        emotional_direction="tense focused pursuit",
        camera_direction=shot.shot_type,
        motion_direction=case["shot"]["motion"],
        style_constraints=str(case.get("style", state.style)),
        success_criteria=case.get("success_criteria", []),
        comfyui_params={"duration_seconds": shot.duration_seconds, "seed_policy": "fixed-per-shot"},
        metadata={"effect_iteration": "v2", "stage": "structured_translated_prompt"},
    )
    state.prompt_package.metadata["iteration"] = "v2"
    state.version = 2
    state.version_diffs.append(
        VersionDiff(
            from_version=1,
            to_version=2,
            changed_shots=[shot.shot_id],
            changed_prompts=[prompt.shot_id],
            field_changes=[
                FieldChange(
                    path="prompt_package.prompts[0]",
                    before=before_prompt,
                    after=prompt.model_dump(mode="json"),
                    change_type="modified",
                    metadata={"source": "effect_structured_prompt"},
                )
            ],
            explanation="Effect demo v2 translated the raw user prompt into a structured generation prompt.",
            metadata={"stage": "structured_translated_prompt"},
        )
    )
    state.touch()


def _build_revision_plan(
    case: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    target_iteration: str,
) -> dict[str, Any]:
    return build_revision_plan_from_target_evaluation(
        evaluation,
        target_iteration=target_iteration,
        success_criteria=case.get("success_criteria", []),
        negative_constraints=case.get("negative_constraints", []),
        patch_catalog=_target_patch_map(),
        lock_catalog=_target_lock_map(),
        composition_policy=(
            "Keep a stable single-shot composition: foreground cyber cat, glowing drone ahead, "
            "wet rooftop surface, rain/night atmosphere, and Shanghai landmark skyline in the background."
        ),
        control_policy=(
            "release generation resources before visual inspection; keep provider, workflow, duration, "
            "seed policy, and composition anchors stable; change only the prompt package"
        ),
    )


def _apply_revision_plan(
    state: ProjectState,
    case: dict[str, Any],
    revision_plan: dict[str, Any],
    *,
    target_version: int,
) -> None:
    before_prompt = state.prompt_package.prompts[0].model_dump(mode="json")
    shot = state.shots[0]
    prompt = state.prompt_package.prompts[0]
    required = case["required_elements"]
    patch_text = " ".join(item["change"] for item in revision_plan["prompt_patches"])
    lock_text = " ".join(item["lock"] for item in revision_plan.get("preservation_locks", []))
    convergence = revision_plan.get("convergence_strategy", {})
    relationship_text = "; ".join(case.get("spatial_relationships", []) + case.get("motion_contracts", []))
    prompt.prompt = (
        f"NON-NEGOTIABLE PHYSICAL TARGETS: {', '.join(required)}. "
        f"REGRESSION GUARD: {convergence.get('regression_guard', '')} "
        f"STABLE COMPOSITION: {convergence.get('composition_policy', '')} "
        f"SCENE: {case['shot']['description']} "
        f"REPAIR FOCUS: {patch_text}. "
        f"PRESERVE LOCKS: {lock_text or 'preserve every target that is already visible'}. "
        f"RELATIONSHIP AND MOTION: {relationship_text}. "
        f"STYLE: {case.get('style', state.style)}."
    )
    prompt.negative_prompt = ", ".join(
        [
            "low quality",
            "distorted anatomy",
            "unreadable text",
            "flicker",
            *revision_plan["negative_prompt_patches"],
        ]
    )
    target_iteration = f"v{target_version}"
    prompt.parameters["effect_iteration"] = target_iteration
    prompt.parameters["effect_stage"] = "physical_compensation_prompt"
    prompt.structured_template = StructuredPromptTemplate(
        character_identity="one cybernetic cat with visible mechanical details and a stable silhouette",
        scene_constraints=case["shot"]["description"],
        physical_constraints=[
            f"Mandatory visible elements: {', '.join(required)}",
            f"Regression guard: {convergence.get('regression_guard', '')}",
            f"Stable composition: {convergence.get('composition_policy', '')}",
            *[item["lock"] for item in revision_plan.get("preservation_locks", [])],
            *case.get("visual_attributes", []),
            *case.get("spatial_relationships", []),
        ],
        action_sequence=relationship_text,
        emotional_direction="tense focused pursuit",
        camera_direction=shot.shot_type,
        motion_direction=case["shot"]["motion"],
        style_constraints=str(case.get("style", state.style)),
        success_criteria=revision_plan["success_criteria"],
        comfyui_params={"duration_seconds": shot.duration_seconds, "seed_policy": "fixed-per-shot"},
        metadata={
            "effect_iteration": target_iteration,
            "stage": "physical_compensation_prompt",
            "revision_intent": revision_plan["revision_intent"],
        },
    )
    state.prompt_package.metadata["iteration"] = target_iteration
    from_version = state.version
    state.version = target_version
    state.version_diffs.append(
        VersionDiff(
            from_version=from_version,
            to_version=target_version,
            changed_shots=[shot.shot_id],
            changed_prompts=[prompt.shot_id],
            field_changes=[
                FieldChange(
                    path="prompt_package.prompts[0]",
                    before=before_prompt,
                    after=prompt.model_dump(mode="json"),
                    change_type="modified",
                    metadata={"source": "effect_revision_plan"},
                )
            ],
            explanation="Effect demo compensation plan strengthened missing physical targets.",
            metadata={"revision_plan": revision_plan},
        )
    )
    state.touch()


def _target_patch_map() -> dict[str, str]:
    return {
        "cyber cat": "show one cybernetic cat with visible metallic details, glowing collar, and running body posture",
        "glowing drone": "place a glowing quadcopter drone two meters ahead of the cat with a cyan light trail",
        "rain": "make rain visible with raindrops, wet fur highlights, puddles, and neon reflections",
        "night": "use dark night sky, high contrast neon lighting, and no daylight cues",
        "rooftop": "show rooftop edge, safety rail, HVAC units, puddles, and high-rise perspective",
        "Shanghai landmark skyline": (
            "add unmistakable Shanghai landmark cues behind the rooftop: Oriental Pearl Tower "
            "sphere silhouette, Shanghai Tower twist silhouette, and Lujiazui neon skyline"
        ),
    }


def _target_lock_map() -> dict[str, str]:
    return {
        "cyber cat": "keep the cyber cat visible in the foreground with the same silhouette and cybernetic details",
        "glowing drone": "keep the glowing drone visible ahead of the cat with a cyan light trail",
        "rain": "keep rain streaks, puddles, and wet reflections visible across the rooftop",
        "night": "keep the scene clearly at night with dark sky and neon contrast",
        "rooftop": "keep the rooftop plane, railing, edge, or HVAC geometry visible as the ground setting",
        "Shanghai landmark skyline": (
            "keep recognizable Shanghai cues in the background, especially Oriental Pearl Tower, "
            "Shanghai Tower, or Lujiazui skyline shapes"
        ),
    }


def _release_generation_resources(generated_result) -> dict[str, Any]:
    if generated_result.provider != "comfyui":
        return {
            "provider": generated_result.provider,
            "status": "skipped",
            "reason": "provider does not hold ComfyUI resources",
        }
    base_url = str(generated_result.metadata.get("capabilities", {}).get("metadata", {}).get("base_url", ""))
    if not base_url and generated_result.shots:
        base_url = str(generated_result.shots[0].metadata.get("comfyui_base_url", ""))
    if not base_url:
        return {"provider": generated_result.provider, "status": "skipped", "reason": "missing base_url"}
    from shotforge.comfyui import ComfyUIClient

    try:
        response = ComfyUIClient(base_url=base_url).free_memory()
    except Exception as exc:
        return {
            "provider": generated_result.provider,
            "status": "failed",
            "base_url": base_url,
            "error": str(exc),
        }
    return {
        "provider": generated_result.provider,
        "status": "released",
        "base_url": base_url,
        "response": response,
    }


def _mark_generation_iteration(generated_result, iteration: str) -> None:
    generated_result.metadata["iteration"] = iteration
    for shot in generated_result.shots:
        shot.metadata["iteration"] = iteration


def _build_comparison(
    case: dict[str, Any],
    *,
    evaluations: list[dict[str, Any]],
    revision_plan: dict[str, Any],
    resource_events: list[dict[str, Any]],
) -> dict[str, Any]:
    return compare_iteration_evaluations(
        case_id=case["case_id"],
        title=case["title"],
        evaluations=evaluations,
        revision_plan=revision_plan,
        resource_events=resource_events,
    )


def _write_effect_outputs(
    *,
    state: ProjectState,
    case: dict[str, Any],
    v1_prompt: dict[str, Any],
    v2_prompt: dict[str, Any],
    v3_prompt: dict[str, Any],
    evaluations: list[dict[str, Any]],
    revision_plan: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, str]:
    root = ExportManager().run_dir(state) / "effect_demo"
    prompt_dir = root / "prompts"
    observation_dir = root / "observations"
    evaluation_dir = root / "evaluations"
    comparison_dir = root / "comparison"
    for directory in [prompt_dir, observation_dir, evaluation_dir, comparison_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "case_targets": root / "acceptance_targets.json",
        "v1_prompt": prompt_dir / "v1_prompt.json",
        "v2_prompt": prompt_dir / "v2_prompt.json",
        "v3_prompt": prompt_dir / "v3_prompt.json",
        "v1_evaluation": evaluation_dir / "v1_evaluation.json",
        "v2_evaluation": evaluation_dir / "v2_evaluation.json",
        "v3_evaluation": evaluation_dir / "v3_evaluation.json",
        "revision_plan": root / "revision_plan.json",
        "comparison_json": comparison_dir / "effect_convergence_report.json",
        "comparison_markdown": comparison_dir / "effect_convergence_report.md",
        "legacy_comparison_json": comparison_dir / "v1_v2_effect_report.json",
        "legacy_comparison_markdown": comparison_dir / "v1_v2_effect_report.md",
    }
    evaluation_by_iteration = {item["iteration"]: item for item in evaluations}
    payloads = {
        "case_targets": _targets_payload(case),
        "v1_prompt": v1_prompt,
        "v2_prompt": v2_prompt,
        "v3_prompt": v3_prompt,
        "v1_evaluation": evaluation_by_iteration["v1"],
        "v2_evaluation": evaluation_by_iteration["v2"],
        "v3_evaluation": evaluation_by_iteration["v3"],
        "revision_plan": revision_plan,
        "comparison_json": comparison,
        "legacy_comparison_json": comparison,
    }
    for key, payload in payloads.items():
        paths[key].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = _comparison_markdown(comparison)
    paths["comparison_markdown"].write_text(markdown, encoding="utf-8")
    paths["legacy_comparison_markdown"].write_text(markdown, encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _comparison_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        f"# {comparison['title']} Effect Report",
        "",
        f"- Case: `{comparison['case_id']}`",
        f"- Status: {comparison['status']}",
        f"- v1 score: {comparison['v1_score']}",
        f"- v2 score: {comparison['v2_score']}",
        f"- v3 score: {comparison['v3_score']}",
        f"- Delta: {comparison['score_delta']}",
        f"- Structured delta: {comparison['structured_delta']}",
        f"- Compensation delta: {comparison['compensation_delta']}",
        f"- Candidate status: {comparison['candidate_status']}",
        f"- Accepted iteration: {comparison['accepted_iteration']}",
        f"- Visual observation available: {comparison['visual_observation_available']}",
        f"- Observers: {', '.join(comparison.get('observer_ids', [])) or 'none'}",
        "",
        "## Iteration Strategy",
        "",
        "- v1: raw user prompt direct generation",
        "- v2: translated structured prompt generation",
        "- v3: physical-target compensation prompt after visual inspection",
        "",
        "## Target Changes",
        "",
        "| Target | v1 | v2 | v3 | v2 Delta | v3 Delta | Frames | Status |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in comparison["target_changes"]:
        lines.append(
            f"| {item['target']} | {item['v1_score']} | {item['v2_score']} | "
            f"{item['v3_score']} | {item['v2_delta']} | {item['v3_delta']} | "
            f"{item['v1_frame_presence']} -> {item['v2_frame_presence']} -> "
            f"{item['v3_frame_presence']} | {item['status']} |"
        )
    lines.extend(
        [
            "",
            "## Revision Plan",
            "",
            comparison["revision_plan"]["revision_intent"],
            "",
        ]
    )
    for patch in comparison["revision_plan"]["prompt_patches"]:
        lines.append(f"- {patch['target']}: {patch['change']}")
    if comparison.get("resource_events"):
        lines.extend(["", "## Resource Events", ""])
        for event in comparison["resource_events"]:
            lines.append(f"- {event.get('provider')}: {event.get('status')} {event.get('base_url', '')}".strip())
    lines.extend(["", "## Regressed", ""])
    if comparison.get("regressed"):
        lines.extend(f"- {target}" for target in comparison["regressed"])
    else:
        lines.append("- none")
    if comparison.get("rejection_reasons"):
        lines.extend(["", "## Candidate Rejection", ""])
        lines.extend(f"- {reason}" for reason in comparison["rejection_reasons"])
        if comparison.get("next_revision_focus"):
            lines.append("")
            lines.append("Next revision focus: " + ", ".join(comparison["next_revision_focus"]))
    lines.extend(["", "## Unresolved", ""])
    if comparison["unresolved"]:
        lines.extend(f"- {target}" for target in comparison["unresolved"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _observation_text(frame: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for value in [
            frame.get("action_summary", ""),
            frame.get("style_summary", ""),
            frame.get("color_summary", ""),
            " ".join(frame.get("detected_elements", [])),
        ]
        if value
    ).lower()


def _aliases_for(element: str) -> list[str]:
    base = element.lower()
    aliases = {
        "cyber cat": ["cyber cat", "cybernetic cat", "cat", "robotic cat", "赛博猫", "猫"],
        "glowing drone": ["glowing drone", "drone", "quadcopter", "cyan light", "发光无人机", "无人机"],
        "rain": ["rain", "rainy", "raindrops", "wet", "puddles", "雨", "雨滴", "湿"],
        "night": ["night", "dark sky", "nighttime", "夜", "夜晚", "雨夜"],
        "rooftop": ["rooftop", "roof", "high-rise", "天台", "屋顶", "楼顶"],
        "shanghai landmark skyline": [
            "shanghai landmark",
            "oriental pearl",
            "oriental pearl tower",
            "shanghai tower",
            "lujiazui",
            "上海地标",
            "东方明珠",
            "上海中心",
            "陆家嘴",
        ],
    }
    return aliases.get(base, [base])


def _contains_alias(text: str, aliases: list[str]) -> bool:
    lowered = text.lower()
    return any(alias.lower() in lowered for alias in aliases)


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")
