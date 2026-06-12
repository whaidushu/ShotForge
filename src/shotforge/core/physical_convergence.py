from __future__ import annotations

from statistics import mean
from typing import Any

from shotforge.core.repair_strategies import RepairStrategyCatalog
from shotforge.core.project_state import EvaluationReport, GeneratedResult, ProjectState


def build_revision_plan_from_target_evaluation(
    evaluation: dict[str, Any],
    *,
    target_iteration: str,
    success_criteria: list[str] | None = None,
    negative_constraints: list[str] | None = None,
    patch_catalog: dict[str, str] | None = None,
    lock_catalog: dict[str, str] | None = None,
    macro_refinement_axes: list[dict[str, str]] | None = None,
    composition_policy: str = "",
    control_policy: str = "",
) -> dict[str, Any]:
    matrix_rows = _matrix_rows(evaluation)
    catalog = RepairStrategyCatalog()
    unresolved_rows = [
        row
        for row in matrix_rows
        if row.get("required", True) and row.get("status") in {"failed", "weak"}
    ]
    issue_targets = [
        str(row.get("target") or row.get("label"))
        for row in unresolved_rows
    ] or [issue["target"] for issue in evaluation.get("issues", [])]
    patch_catalog = patch_catalog or {}
    lock_catalog = lock_catalog or {}
    macro_refinement_axes = macro_refinement_axes or []
    if unresolved_rows:
        prompt_patches = []
        for row in unresolved_rows:
            target = str(row.get("target") or row.get("label"))
            patch = catalog.prompt_patch(row)
            if target in patch_catalog:
                patch["change"] = patch_catalog[target]
            prompt_patches.append(patch)
    else:
        prompt_patches = [
            {
                "target": target,
                "change": patch_catalog.get(
                    target,
                    f"make {target} clearly visible and measurable in the frame",
                ),
            }
            for target in issue_targets
        ]
    preservation_locks = _preservation_locks(
        evaluation=evaluation,
        issue_targets=issue_targets,
        lock_catalog=lock_catalog,
        catalog=catalog,
    )
    negative_patches = [
        value
        for row in unresolved_rows
        for value in [catalog.negative_patch(row)]
        if value
    ]
    revision_intent = "make missing or weak physical targets visible and measurable"
    refinement_mode = "repair_missing_or_weak_targets"
    if not prompt_patches:
        if macro_refinement_axes:
            revision_intent = (
                "upgrade an already strong source iteration with macro-level motion, staging, "
                "and silhouette refinements"
            )
            refinement_mode = "high_score_macro_refinement"
            prompt_patches = [
                {
                    "target": axis.get("target", "macro refinement"),
                    "change": axis.get("change", "strengthen the scene at the composition level"),
                    "refinement_type": axis.get("type", "macro"),
                }
                for axis in macro_refinement_axes
            ]
        else:
            prompt_patches = [
                {
                    "target": "all targets",
                    "change": "preserve all required elements while strengthening the action relationship",
                }
            ]
    return {
        "revision_intent": revision_intent,
        "source_iteration": evaluation.get("iteration", ""),
        "target_iteration": target_iteration,
        "prompt_patches": prompt_patches,
        "preservation_locks": preservation_locks,
        "negative_prompt_patches": [*(negative_constraints or []), *negative_patches],
        "success_criteria": success_criteria or [],
        "convergence_strategy": {
            "refinement_mode": refinement_mode,
            "repair_targets": issue_targets,
            "repair_target_ids": [
                str(row.get("target_id", ""))
                for row in unresolved_rows
                if row.get("target_id")
            ],
            "macro_refinement_axes": macro_refinement_axes,
            "locked_targets": [item["target"] for item in preservation_locks],
            "target_matrix_available": bool(matrix_rows),
            "regression_guard": (
                "Do not improve one physical target by removing or weakening a target that was "
                "already visible in the source iteration."
            ),
            "composition_policy": composition_policy
            or "Keep the composition stable while changing only the missing or weak physical targets.",
        },
        "control_policy": control_policy
        or "keep provider, workflow, duration, seed policy, and composition anchors stable; change only the prompt package",
    }


def _matrix_rows(evaluation: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = evaluation.get("target_matrix", {})
    rows = matrix.get("target_scores", []) if isinstance(matrix, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def _preservation_locks(
    *,
    evaluation: dict[str, Any],
    issue_targets: list[str],
    lock_catalog: dict[str, str],
    catalog: RepairStrategyCatalog,
) -> list[dict[str, Any]]:
    matrix_rows = _matrix_rows(evaluation)
    if matrix_rows:
        return [
            {
                **catalog.preservation_lock(row),
                "lock": lock_catalog.get(
                    str(row.get("target") or row.get("label")),
                    catalog.preservation_lock(row)["lock"],
                ),
            }
            for row in matrix_rows
            if row.get("target") not in issue_targets
            and row.get("required", True)
            and float(row.get("score", 0.0) or 0.0) >= 0.68
        ]
    return [
        {
            "target": item["target"],
            "score": item["score"],
            "frame_presence": f"{len(item.get('frame_hits', []))}/{item.get('sampled_frame_count', 0)}",
            "lock": lock_catalog.get(
                item["target"],
                f"preserve {item['target']} with at least the same visibility as the source iteration",
            ),
        }
        for item in evaluation.get("target_scores", [])
        if item["target"] not in issue_targets and item.get("score", 0) >= 0.68
    ]


def compare_iteration_evaluations(
    *,
    case_id: str,
    title: str,
    evaluations: list[dict[str, Any]],
    revision_plan: dict[str, Any],
    resource_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    by_iteration = {item["iteration"]: item for item in evaluations}
    if not {"v1", "v2", "v3"}.issubset(by_iteration):
        raise ValueError("compare_iteration_evaluations requires v1, v2, and v3 evaluations.")
    v1_evaluation = by_iteration["v1"]
    v2_evaluation = by_iteration["v2"]
    v3_evaluation = by_iteration["v3"]
    v1_by_target = {item["target"]: item for item in v1_evaluation["target_scores"]}
    v2_by_target = {item["target"]: item for item in v2_evaluation["target_scores"]}
    changes = []
    repaired = []
    unresolved = []
    regressed = []
    for item in v3_evaluation["target_scores"]:
        target = item["target"]
        v1_item = v1_by_target[target]
        v2_item = v2_by_target[target]
        v2_delta = round(v2_item["score"] - v1_item["score"], 3)
        v3_delta = round(item["score"] - v2_item["score"], 3)
        row = {
            "target": target,
            "v1_score": v1_item["score"],
            "v2_score": v2_item["score"],
            "v3_score": item["score"],
            "v2_delta": v2_delta,
            "v3_delta": v3_delta,
            "v1_frame_presence": _frame_presence(v1_item),
            "v2_frame_presence": _frame_presence(v2_item),
            "v3_frame_presence": _frame_presence(item),
            "status": "improved" if v3_delta > 0.05 else "unchanged" if v3_delta >= -0.02 else "regressed",
        }
        changes.append(row)
        if row["status"] == "regressed":
            regressed.append(target)
        if item["status"] == "passed" and v2_item["status"] != "passed":
            repaired.append(target)
        elif item["status"] != "passed":
            unresolved.append(target)
    structured_delta = round(v2_evaluation["overall_score"] - v1_evaluation["overall_score"], 3)
    compensation_delta = round(v3_evaluation["overall_score"] - v2_evaluation["overall_score"], 3)
    total_delta = round(v3_evaluation["overall_score"] - v1_evaluation["overall_score"], 3)
    gate = candidate_gate(
        source_score=v2_evaluation["overall_score"],
        candidate_score=v3_evaluation["overall_score"],
        regressed_targets=regressed,
        unresolved_targets=unresolved,
        revision_plan=revision_plan,
    )
    return {
        "case_id": case_id,
        "title": title,
        "v1_score": v1_evaluation["overall_score"],
        "v2_score": v2_evaluation["overall_score"],
        "v3_score": v3_evaluation["overall_score"],
        "score_delta": total_delta,
        "structured_delta": structured_delta,
        "compensation_delta": compensation_delta,
        "status": (
            "converged"
            if gate["candidate_status"] == "accepted" and not unresolved and not regressed
            else "improved"
            if gate["candidate_status"] == "accepted" and total_delta > 0.05
            else "needs_more_work"
        ),
        **gate,
        "next_revision_focus": sorted(set(unresolved + regressed)),
        "visual_observation_available": any(item["visual_observation_available"] for item in evaluations),
        "observer_ids": sorted({str(item.get("observer_id", "")) for item in evaluations if item.get("observer_id")}),
        "target_changes": changes,
        "repaired": repaired,
        "unresolved": unresolved,
        "regressed": regressed,
        "revision_plan": revision_plan,
        "resource_events": resource_events or [],
        "v1": v1_evaluation,
        "v2": v2_evaluation,
        "v3": v3_evaluation,
        "iterations": evaluations,
    }


def build_report_target_evaluation(
    state: ProjectState,
    report: EvaluationReport,
    generated_result: GeneratedResult,
    *,
    iteration: str | None = None,
) -> dict[str, Any]:
    required = _required_elements(state)
    observed = _observed_elements(generated_result)
    prompt_text = _prompt_text(state)
    issue_missing = _missing_elements_from_issues(report)
    target_scores = []
    for target in required:
        target_lower = target.lower()
        observed_hit = any(target_lower == item.lower() for item in observed)
        prompt_hit = target_lower in prompt_text.lower()
        missing = target in issue_missing or (not observed_hit and _has_visual_observation(generated_result))
        if observed_hit:
            score = 1.0
        elif missing:
            score = 0.25
        elif prompt_hit and not _has_visual_observation(generated_result):
            score = 0.62
        elif prompt_hit:
            score = 0.45
        else:
            score = 0.2
        target_scores.append(
            {
                "target": target,
                "aliases": [target],
                "score": round(score, 3),
                "visual_score": 1.0 if observed_hit else 0.0,
                "prompt_score": 0.8 if prompt_hit else 0.0,
                "frame_hits": [0] if observed_hit else [],
                "sampled_frame_count": 1 if _has_visual_observation(generated_result) else 0,
                "generated_hit": observed_hit,
                "prompt_hit": prompt_hit,
                "status": "passed" if score >= 0.75 else "weak" if score >= 0.45 else "failed",
            }
        )
    issues = [
        {
            "target": item["target"],
            "type": "missing_or_weak_physical_target",
            "severity": "high" if item["score"] < 0.45 else "medium",
            "evidence": f"generated_hit={item['generated_hit']}, prompt_hit={item['prompt_hit']}",
        }
        for item in target_scores
        if item["status"] != "passed"
    ]
    overall_score = round(mean(item["score"] for item in target_scores), 3) if target_scores else 1.0
    return {
        "iteration": iteration or f"v{report.version_id}",
        "version": report.version_id,
        "evaluation_id": report.evaluation_id,
        "generated_result_id": generated_result.generated_result_id,
        "provider": generated_result.provider,
        "video_refs": generated_result.artifact_refs,
        "visual_observation_available": _has_visual_observation(generated_result),
        "observer_id": _observer_id(state, generated_result),
        "sampled_frame_count": sum(len(shot.frame_observations) for shot in generated_result.shots),
        "overall_score": overall_score,
        "target_scores": target_scores,
        "issues": issues,
        "required_elements": required,
        "observed_elements": observed,
        "missing_elements": sorted(issue_missing),
    }


def compare_report_target_evaluations(
    source: dict[str, Any],
    candidate: dict[str, Any],
    *,
    revision_plan: dict[str, Any],
) -> dict[str, Any]:
    source_by_target = {item["target"]: item for item in source.get("target_scores", [])}
    regressed = []
    repaired = []
    unresolved = []
    target_changes = []
    for item in candidate.get("target_scores", []):
        before = source_by_target.get(item["target"], {"score": 0.0, "status": "failed"})
        delta = round(item["score"] - before["score"], 3)
        if delta < -0.02:
            regressed.append(item["target"])
        if item["status"] == "passed" and before.get("status") != "passed":
            repaired.append(item["target"])
        elif item["status"] != "passed":
            unresolved.append(item["target"])
        target_changes.append(
            {
                "target": item["target"],
                "source_score": before["score"],
                "candidate_score": item["score"],
                "delta": delta,
                "status": "improved" if delta > 0.05 else "unchanged" if delta >= -0.02 else "regressed",
            }
        )
    gate = candidate_gate(
        source_score=source.get("overall_score", 0.0),
        candidate_score=candidate.get("overall_score", 0.0),
        regressed_targets=regressed,
        unresolved_targets=unresolved,
        revision_plan=revision_plan,
    )
    return {
        **gate,
        "source_iteration": source.get("iteration", ""),
        "candidate_iteration": candidate.get("iteration", ""),
        "source_score": source.get("overall_score", 0.0),
        "candidate_score": candidate.get("overall_score", 0.0),
        "score_delta": round(candidate.get("overall_score", 0.0) - source.get("overall_score", 0.0), 3),
        "target_changes": target_changes,
        "repaired": repaired,
        "unresolved": unresolved,
        "regressed": regressed,
        "next_revision_focus": sorted(set(unresolved + regressed)),
    }


def candidate_gate(
    *,
    source_score: float,
    candidate_score: float,
    regressed_targets: list[str],
    unresolved_targets: list[str],
    revision_plan: dict[str, Any],
    score_drop_tolerance: float = -0.02,
) -> dict[str, Any]:
    score_delta = round(candidate_score - source_score, 3)
    locked_targets = set(revision_plan.get("convergence_strategy", {}).get("locked_targets", []))
    locked_regressions = [target for target in regressed_targets if target in locked_targets]
    rejection_reasons = []
    if locked_regressions:
        rejection_reasons.append(
            "candidate regressed locked targets: " + ", ".join(locked_regressions)
        )
    if score_delta < score_drop_tolerance:
        rejection_reasons.append(f"candidate score dropped from source iteration by {score_delta}")
    candidate_status = "rejected" if rejection_reasons else "accepted"
    source_iteration = str(revision_plan.get("source_iteration", "source"))
    target_iteration = str(revision_plan.get("target_iteration", "candidate"))
    return {
        "candidate_status": candidate_status,
        "accepted_iteration": source_iteration if candidate_status == "rejected" else target_iteration,
        "rejected_iteration": target_iteration if candidate_status == "rejected" else "",
        "rejection_reasons": rejection_reasons,
        "locked_regressions": locked_regressions,
    }


def _frame_presence(item: dict[str, Any]) -> str:
    return f"{len(item.get('frame_hits', []))}/{item.get('sampled_frame_count', 0)}"


def _required_elements(state: ProjectState) -> list[str]:
    values = state.metadata.get("physical_targets", {}).get("required_elements", [])
    if isinstance(values, list):
        return [str(item) for item in values]
    return []


def _observed_elements(generated_result: GeneratedResult) -> list[str]:
    observed = []
    for shot in generated_result.shots:
        for item in shot.detected_elements:
            text = str(item)
            if text and text not in observed:
                observed.append(text)
    return observed


def _prompt_text(state: ProjectState) -> str:
    parts = []
    for prompt in state.prompt_package.prompts:
        parts.append(prompt.prompt)
        if prompt.structured_template:
            parts.append(prompt.structured_template.render())
        parts.append(prompt.negative_prompt)
    return " ".join(parts)


def _missing_elements_from_issues(report: EvaluationReport) -> set[str]:
    missing = set()
    for issue in report.issues:
        values = issue.metadata.get("missing_elements", [])
        if isinstance(values, list):
            missing.update(str(item) for item in values)
    return missing


def _has_visual_observation(generated_result: GeneratedResult) -> bool:
    return any(shot.frame_observations for shot in generated_result.shots)


def _observer_id(state: ProjectState, generated_result: GeneratedResult) -> str:
    for report in state.observation_reports:
        if report.generated_result_id == generated_result.generated_result_id:
            return report.observer_id
    return ""
