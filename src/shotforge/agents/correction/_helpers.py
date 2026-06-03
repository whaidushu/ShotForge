from __future__ import annotations

from functools import lru_cache
import json
from importlib.resources import files

from shotforge.core.project_state import CorrectionOperation, CorrectionPlan, Issue, ProjectState
from shotforge.i18n import get_translator


def target_shot_ids(state: ProjectState, plan: CorrectionPlan) -> list[str]:
    shot_ids = plan.metadata.get("shot_ids", [])
    if isinstance(shot_ids, list) and shot_ids:
        return [str(shot_id) for shot_id in shot_ids]
    issues = target_issues(state, plan)
    inferred = sorted({issue.shot_id for issue in issues if issue.shot_id})
    return inferred or [shot.shot_id for shot in state.shots[:1]]


def target_issues(state: ProjectState, plan: CorrectionPlan) -> list[Issue]:
    wanted = set(plan.target_issue_ids)
    return [issue for issue in state.issue_history if issue.issue_id in wanted]


def localized_note(
    language: str,
    key: str,
    plan: CorrectionPlan,
    issues: list[Issue],
) -> str:
    issue_summary = "; ".join(issue.description for issue in issues[:3])
    translator = get_translator()
    return _strategy_text(language, key) or translator.t(
        language,
        key,
        strategy=plan.correction_strategy,
        issues=issue_summary or "-",
    )


def story_beat_upgrade(
    state: ProjectState,
    shot_id: str,
    correction_type: str,
    fallback: str,
) -> str:
    shot = next((item for item in state.shots if item.shot_id == shot_id), None)
    beat = shot.metadata.get("story_beat", {}) if shot else {}
    value = beat.get(f"{correction_type}_upgrade")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def prompt_revision_note(
    state: ProjectState,
    shot_id: str,
    correction_type: str,
    fallback: str,
) -> str:
    shot = next((item for item in state.shots if item.shot_id == shot_id), None)
    upgrade = story_beat_upgrade(state, shot_id, correction_type, fallback)
    if not shot:
        return upgrade
    anchors = ", ".join(shot.key_visuals[:6])
    if anchors:
        return (
            f"Revision target for {shot_id}: {upgrade} "
            f"Keep these visible anchors measurable on screen: {anchors}."
        )
    return f"Revision target for {shot_id}: {upgrade}"


def operation(
    operation_type: str,
    target_id: str,
    field_path: str,
    value: str | list[str],
    rationale: str,
    metadata: dict | None = None,
) -> CorrectionOperation:
    return CorrectionOperation(
        operation_type=operation_type,
        target_id=target_id,
        field_path=field_path,
        value=value,
        rationale=rationale,
        metadata=metadata or {},
    )


def effect_contracts_for_shot(issues: list[Issue], shot_id: str, language: str) -> list[str]:
    contracts = []
    for issue in issues:
        if issue.shot_id != shot_id:
            continue
        contracts.append(effect_contract_for_issue(issue, language))
    seen = []
    for contract in contracts:
        if contract and contract not in seen:
            seen.append(contract)
    return seen


def effect_contract_for_issue(issue: Issue, language: str) -> str:
    dimension_id = issue.dimension_id
    evidence = issue.evidence
    prefix = "效果契约" if language == "zh" else "EFFECT CONTRACT"
    if dimension_id == "frame_action_consistency":
        return (
            f"{prefix}: ACTION CONTINUITY - keep one continuous action across the whole clip; "
            "show a visible start pose, one readable movement direction, and a clear end pose; "
            "do not let the action mutate into a different action."
        )
    if dimension_id == "frame_element_consistency":
        return (
            f"{prefix}: ELEMENT LOCK - the same required props and scene anchors must stay visible "
            "from first frame to last frame; no object morphing, replacement, or disappearance."
        )
    if dimension_id == "face_identity_consistency":
        return (
            f"{prefix}: IDENTITY LOCK - keep the same face, silhouette, wardrobe, and body shape "
            "across every frame; no face swap or identity drift."
        )
    if dimension_id == "color_alignment":
        colors = _metadata_list(issue, "expected_colors") or _extract_list_from_evidence(
            evidence,
            "expected_colors",
        )
        color_text = ", ".join(colors) if colors else "named colors"
        return (
            f"{prefix}: COLOR LOCK - preserve {color_text} as visible, high-saturation, persistent "
            "screen colors throughout the shot; keep glow/material color stable."
        )
    if dimension_id == "subject_count":
        count = issue.metadata.get("expected_subject_count")
        count_text = str(count) if count is not None else "the requested number of"
        return (
            f"{prefix}: SUBJECT COUNT LOCK - show exactly {count_text} primary subject(s); "
            "do not duplicate, merge, hide, or drop the main subject."
        )
    if dimension_id == "element_presence":
        elements = _metadata_list(issue, "expected_elements") or _extract_list_from_evidence(
            evidence,
            "expected_elements",
        )
        element_text = ", ".join(elements[:5]) if elements else "all required visible elements"
        return (
            f"{prefix}: ELEMENT CHECKLIST - make these elements clearly visible: {element_text}; "
            "place them as foreground or midground anchors, not vague background texture."
        )
    if dimension_id == "element_description":
        return (
            f"{prefix}: PHYSICAL SPEC - state concrete subject, prop, color, material, location, "
            "and success criteria so the generated result can be visually checked."
        )
    if dimension_id == "action_clarity":
        return (
            f"{prefix}: ACTION READABILITY - use one clear verb, one target object, and one visible "
            "reaction/outcome; avoid abstract motion language."
        )
    return (
        f"{prefix}: make the target issue visibly measurable in the generated frames. "
        f"Target dimension: {dimension_id}."
    )


def negative_constraints_for_issues(issues: list[Issue]) -> str:
    dimensions = {issue.dimension_id for issue in issues}
    negatives = []
    if dimensions.intersection({"frame_action_consistency", "action_clarity"}):
        negatives.extend(["random action changes", "unclear movement", "action morphing"])
    if dimensions.intersection({"frame_element_consistency", "element_presence"}):
        negatives.extend(["object morphing", "missing props", "changing scene anchors"])
    if "face_identity_consistency" in dimensions:
        negatives.extend(["face swap", "identity drift", "different person"])
    if "color_alignment" in dimensions:
        negatives.extend(["washed out color", "color shift", "missing glow"])
    if "subject_count" in dimensions:
        negatives.extend(["extra subject", "duplicated subject", "missing subject"])
    return ", ".join(dict.fromkeys(negatives))


def _metadata_list(issue: Issue, key: str) -> list[str]:
    value = issue.metadata.get(key)
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _extract_list_from_evidence(evidence: str, key: str) -> list[str]:
    marker = f"{key}=["
    if marker not in evidence:
        return []
    start = evidence.find(marker) + len(marker)
    end = evidence.find("]", start)
    if end < 0:
        return []
    raw = evidence[start:end]
    return [part.strip().strip("'\"") for part in raw.split(",") if part.strip()]


@lru_cache(maxsize=1)
def _strategy_book() -> dict:
    path = files("shotforge.knowledge").joinpath("correction_strategies.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _strategy_text(language: str, key: str) -> str:
    prefix = "agents.correction."
    if not key.startswith(prefix):
        return ""
    parts = key.removeprefix(prefix).split(".")
    if len(parts) != 2:
        return ""
    correction_type, note_key = parts
    entry = _strategy_book().get("strategies", {}).get(correction_type, {})
    value = entry.get("notes", {}).get(note_key, {}).get(language)
    if isinstance(value, str):
        return value
    return ""
