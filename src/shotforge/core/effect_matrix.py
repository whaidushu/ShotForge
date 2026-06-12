from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from shotforge.core.effect_contract import EffectContract, EffectTarget


TargetStatus = Literal["passed", "weak", "failed", "unknown"]
FailureReason = Literal[
    "none",
    "prompt_missing",
    "prompt_weak",
    "observation_missing",
    "model_ignored",
    "control_needed",
    "unresolved",
]


class EffectTargetScore(BaseModel):
    target_id: str
    target: str
    label: str
    layer: str
    target_type: str
    shot_id: str = "shot_001"
    required: bool = True
    threshold: float = 0.75
    score: float = 0.0
    visual_score: float = 0.0
    prompt_score: float = 0.0
    status: TargetStatus = "unknown"
    failure_reason: FailureReason = "unresolved"
    evidence: list[str] = Field(default_factory=list)
    frame_hits: list[int] = Field(default_factory=list)
    sampled_frame_count: int = 0
    generated_hit: bool = False
    prompt_hit: bool = False
    repair_suggestion: str = ""
    locked: bool = False
    lock_suggestion: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class EffectTargetMatrix(BaseModel):
    matrix_id: str
    contract_id: str
    iteration: str
    overall_score: float = 0.0
    target_scores: list[EffectTargetScore] = Field(default_factory=list)
    unresolved_targets: list[str] = Field(default_factory=list)
    locked_targets: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_effect_target_matrix(
    contract: EffectContract,
    evaluation: dict[str, Any],
) -> EffectTargetMatrix:
    score_rows = evaluation.get("target_scores", []) or []
    target_check_rows = _target_check_scores(evaluation)
    matched_indexes: set[int] = set()
    scores: list[EffectTargetScore] = []
    for target in contract.targets:
        score, index = _match_score(target, score_rows)
        if index is not None:
            matched_indexes.add(index)
        check_score = _match_target_check_score(target, target_check_rows)
        merged_score = {**(score or {}), **(check_score or {})}
        scores.append(_score_from_target(target, merged_score, evaluation=evaluation))

    for index, score in enumerate(score_rows):
        if index in matched_indexes or not isinstance(score, dict):
            continue
        scores.append(_score_from_unmatched(score, contract=contract, evaluation=evaluation))

    unresolved = [row.target for row in scores if row.required and row.status != "passed"]
    locked = [row.target for row in scores if row.locked]
    overall = evaluation.get("overall_score")
    if overall is None and scores:
        overall = round(sum(row.score for row in scores) / len(scores), 3)
    return EffectTargetMatrix(
        matrix_id=f"{contract.contract_id}.{evaluation.get('iteration', 'iteration')}",
        contract_id=contract.contract_id,
        iteration=str(evaluation.get("iteration", "")),
        overall_score=float(overall or 0.0),
        target_scores=scores,
        unresolved_targets=unresolved,
        locked_targets=locked,
        metadata={
            "generated_result_id": evaluation.get("generated_result_id", ""),
            "visual_observation_available": evaluation.get("visual_observation_available", False),
            "observer_id": evaluation.get("observer_id", ""),
        },
    )


def matrix_to_revision_input(matrix: EffectTargetMatrix) -> dict[str, Any]:
    return {
        "iteration": matrix.iteration,
        "overall_score": matrix.overall_score,
        "target_scores": [row.model_dump(mode="json") for row in matrix.target_scores],
        "issues": [
            {
                "target": row.target,
                "target_id": row.target_id,
                "type": "effect_contract_target_unresolved",
                "severity": "high" if row.score < 0.45 else "medium",
                "failure_reason": row.failure_reason,
                "evidence": "; ".join(row.evidence),
                "repair_suggestion": row.repair_suggestion,
            }
            for row in matrix.target_scores
            if row.required and row.status != "passed"
        ],
        "target_matrix": matrix.model_dump(mode="json"),
    }


def _score_from_target(
    target: EffectTarget,
    score: dict[str, Any],
    *,
    evaluation: dict[str, Any],
) -> EffectTargetScore:
    has_score = bool(score)
    raw_score = float(score.get("score", 0.0) or 0.0)
    prompt_hit = bool(score.get("prompt_hit", False))
    generated_hit = bool(score.get("generated_hit", False))
    frame_hits = [int(item) for item in score.get("frame_hits", []) if isinstance(item, int)]
    sampled = int(score.get("sampled_frame_count", 0) or 0)
    status = (
        _status(raw_score, target.threshold, str(score.get("status", "")))
        if has_score
        else "unknown"
    )
    explicit_failure_reason = str(score.get("failure_reason", "")).strip()
    if explicit_failure_reason:
        failure_reason = _normalize_failure_reason(explicit_failure_reason)
    elif has_score:
        failure_reason = _failure_reason(
            status=status,
            prompt_hit=prompt_hit,
            generated_hit=generated_hit,
            sampled_frame_count=sampled,
            score=raw_score,
            threshold=target.threshold,
        )
    else:
        failure_reason = "unresolved"
    label = str(score.get("target") or target.label)
    return EffectTargetScore(
        target_id=target.target_id,
        target=label,
        label=target.label,
        layer=target.layer,
        target_type=target.target_type,
        shot_id=target.shot_id,
        required=target.required,
        threshold=target.threshold,
        score=round(raw_score, 3),
        visual_score=float(score.get("visual_score", 0.0) or 0.0),
        prompt_score=float(score.get("prompt_score", 0.0) or 0.0),
        status=status,
        failure_reason=failure_reason,
        evidence=_evidence(score, target, evaluation),
        frame_hits=frame_hits,
        sampled_frame_count=sampled,
        generated_hit=generated_hit,
        prompt_hit=prompt_hit,
        repair_suggestion=str(score.get("repair_suggestion") or _repair_suggestion(target, failure_reason)),
        locked=status == "passed" and target.lock_policy == "lock_when_passed",
        lock_suggestion=_lock_suggestion(target),
        metadata={
            **score.get("metadata", {}),
            "evidence_rule": target.evidence_rule,
            "repair_strategy": target.repair_strategy,
        },
    )


def _score_from_unmatched(
    score: dict[str, Any],
    *,
    contract: EffectContract,
    evaluation: dict[str, Any],
) -> EffectTargetScore:
    label = str(score.get("target", "unmatched target"))
    target = EffectTarget(
        target_id=f"unmatched.{_safe_id(label)}",
        label=label,
        target_type="object",
        shot_id=contract.shot_id,
        required=True,
    )
    return _score_from_target(target, score, evaluation=evaluation)


def _match_score(target: EffectTarget, rows: list[Any]) -> tuple[dict[str, Any] | None, int | None]:
    labels = {target.label.lower(), *(alias.lower() for alias in target.aliases)}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        value = str(row.get("target", "")).lower()
        aliases = {str(alias).lower() for alias in row.get("aliases", [])}
        if value in labels or labels.intersection(aliases):
            return row, index
    return None, None


def _target_check_scores(evaluation: dict[str, Any]) -> list[dict[str, Any]]:
    frames = evaluation.get("frame_observations", []) or []
    grouped: dict[str, list[dict[str, Any]]] = {}
    label_grouped: dict[str, list[dict[str, Any]]] = {}
    for frame_index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue
        for check in frame.get("target_checks", []) or []:
            if not isinstance(check, dict):
                continue
            row = {**check, "frame_index": frame_index}
            target_id = str(check.get("target_id", "")).lower()
            label = str(check.get("label", "")).lower()
            if target_id:
                grouped.setdefault(target_id, []).append(row)
            if label:
                label_grouped.setdefault(label, []).append(row)
    result = []
    for checks in [*grouped.values(), *label_grouped.values()]:
        if not checks:
            continue
        result.append(_summarize_target_checks(checks))
    return result


def _match_target_check_score(
    target: EffectTarget,
    rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    labels = {target.label.lower(), *(alias.lower() for alias in target.aliases)}
    target_id = target.target_id.lower()
    for row in rows:
        row_target_id = str(row.get("target_id", "")).lower()
        row_label = str(row.get("target", row.get("label", ""))).lower()
        if row_target_id == target_id or row_label in labels:
            return row
    return None


def _summarize_target_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    visible_checks = [check for check in checks if bool(check.get("visible", False))]
    frame_hits = [int(check["frame_index"]) for check in visible_checks if isinstance(check.get("frame_index"), int)]
    scores = [float(check.get("score", 0.0) or 0.0) for check in checks]
    score = round(sum(scores) / len(scores), 3) if scores else 0.0
    failure_reason = next(
        (
            str(check.get("failure_reason", ""))
            for check in checks
            if str(check.get("failure_reason", "")).strip()
            and str(check.get("failure_reason", "")) != "none"
        ),
        "",
    )
    suggested_repair = next(
        (
            str(check.get("suggested_repair", ""))
            for check in checks
            if str(check.get("suggested_repair", "")).strip()
        ),
        "",
    )
    label = str(checks[0].get("label", ""))
    return {
        "target_id": str(checks[0].get("target_id", "")),
        "target": label,
        "label": label,
        "target_type": str(checks[0].get("target_type", "")),
        "score": score,
        "visual_score": score,
        "frame_hits": frame_hits,
        "sampled_frame_count": len(checks),
        "generated_hit": bool(frame_hits),
        "status": "passed" if score >= 0.75 else "weak" if score >= 0.45 else "failed",
        "failure_reason": failure_reason,
        "repair_suggestion": suggested_repair,
        "metadata": {
            "target_check_evidence": [
                str(check.get("evidence", ""))
                for check in checks
                if str(check.get("evidence", "")).strip()
            ],
            "target_check_count": len(checks),
        },
    }


def _status(score: float, threshold: float, explicit_status: str) -> TargetStatus:
    if explicit_status in {"passed", "weak", "failed"}:
        return explicit_status  # type: ignore[return-value]
    if score >= threshold:
        return "passed"
    if score >= max(0.45, threshold - 0.25):
        return "weak"
    return "failed"


def _failure_reason(
    *,
    status: TargetStatus,
    prompt_hit: bool,
    generated_hit: bool,
    sampled_frame_count: int,
    score: float,
    threshold: float,
) -> FailureReason:
    if status == "passed":
        return "none"
    if sampled_frame_count == 0:
        return "observation_missing"
    if not prompt_hit:
        return "prompt_missing"
    if prompt_hit and not generated_hit and score < threshold:
        return "model_ignored" if score >= 0.35 else "control_needed"
    if prompt_hit and generated_hit:
        return "prompt_weak"
    return "unresolved"


def _normalize_failure_reason(value: str) -> FailureReason:
    normalized = value.strip().lower()
    if normalized in {
        "none",
        "prompt_missing",
        "prompt_weak",
        "observation_missing",
        "model_ignored",
        "control_needed",
        "unresolved",
    }:
        return normalized  # type: ignore[return-value]
    return "unresolved"


def _repair_suggestion(target: EffectTarget, failure_reason: FailureReason) -> str:
    if failure_reason == "none":
        return ""
    if target.target_type == "setting":
        return (
            f"make {target.label} visible through concrete environment anchors, "
            "background geometry, and readable scene placement"
        )
    if target.target_type == "spatial_relation":
        return (
            f"make the spatial relation explicit: {target.label}; use screen position, "
            "front/back order, and separated silhouettes"
        )
    if target.target_type == "action":
        return (
            f"make the action readable: {target.label}; describe actor, target, direction, "
            "start state, and visible motion result"
        )
    if target.target_type == "negative_constraint":
        return f"avoid this failure mode explicitly in the negative prompt: {target.label}"
    if failure_reason == "control_needed":
        return (
            f"{target.label} may need reference image, mask, pose, depth, or workflow-level control "
            "instead of prompt-only repair"
        )
    return f"make {target.label} clearly visible, separable, and measurable in the frame"


def _lock_suggestion(target: EffectTarget) -> str:
    return f"preserve {target.label} with at least the same visibility in the next iteration"


def _evidence(
    score: dict[str, Any],
    target: EffectTarget,
    evaluation: dict[str, Any],
) -> list[str]:
    evidence = [
        f"score={round(float(score.get('score', 0.0) or 0.0), 3)}",
        f"threshold={target.threshold}",
        f"prompt_hit={bool(score.get('prompt_hit', False))}",
        f"generated_hit={bool(score.get('generated_hit', False))}",
        f"frames={len(score.get('frame_hits', []) or [])}/{score.get('sampled_frame_count', 0)}",
    ]
    evidence.extend(
        str(item)
        for item in score.get("metadata", {}).get("target_check_evidence", [])
        if str(item).strip()
    )
    if not evaluation.get("visual_observation_available", False):
        evidence.append("visual_observation_available=false")
    return evidence


def _safe_id(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_") or "target"
