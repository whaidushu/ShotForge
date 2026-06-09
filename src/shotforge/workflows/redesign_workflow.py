from __future__ import annotations

from shotforge.agents.correction import build_default_correction_registry
from shotforge.agents.evaluation import CorrectionRouter
from shotforge.agents.structuring import OutputStructuringAgent
from shotforge.core.physical_convergence import (
    build_report_target_evaluation,
    build_revision_plan_from_target_evaluation,
    compare_report_target_evaluations,
)
from shotforge.core.project_state import CorrectionPatch, EvaluationReport, ProjectState
from shotforge.core.regression_check import RegressionCheckBuilder, ScoreDeltaBuilder
from shotforge.core.trace_log import TraceLog
from shotforge.workflows.evaluation_workflow import (
    observe_generation,
    run_evaluation,
    run_generation,
    run_verification,
)
from shotforge.workflows.redesign_planning_workflow import run_redesign_planning


def run_redesign(
    state: ProjectState,
    report: EvaluationReport | None = None,
    reevaluate: bool = True,
    generator_provider_id: str | None = None,
) -> ProjectState:
    with TraceLog(state).span("redesign_workflow"):
        source_report = report or state.evaluation_reports[-1]
        source_generation = _generated_result_for_report(state, source_report)
        physical_source = (
            build_report_target_evaluation(state, source_report, source_generation)
            if source_generation is not None
            else {}
        )
        physical_revision_plan = (
            build_revision_plan_from_target_evaluation(
                physical_source,
                target_iteration=f"v{state.version + 1}",
                composition_policy="Preserve already visible physical targets while repairing missing or weak targets.",
            )
            if physical_source.get("target_scores")
            else {}
        )
        plans = run_redesign_planning(state, report=source_report)
        _attach_physical_plan(plans, physical_revision_plan)
        target_version = state.version + 1
        registry = build_default_correction_registry()
        router = CorrectionRouter()
        patches: list[CorrectionPatch] = []
        skipped: list[dict[str, str]] = []
        routes: list[dict[str, str]] = []
        for plan in plans:
            route = router.route(plan, registry)
            routes.append(
                {
                    "plan_id": route.plan_id,
                    "correction_type": route.correction_type,
                    "selected_agent": route.selected_agent,
                    "status": route.status,
                    "reason": route.reason,
                }
            )
            if route.status != "routed":
                plan.status = "skipped"
                skipped.append({"plan_id": plan.plan_id, "reason": route.reason})
                continue
            agent = registry.get(route.correction_type)
            if agent is None:
                plan.status = "skipped"
                skipped.append({"plan_id": plan.plan_id, "reason": "route_agent_missing"})
                continue
            plan.selected_agent = route.selected_agent
            patches.append(agent.apply(state, plan, target_version=target_version))
        next_state = OutputStructuringAgent().structure(state, patches, reason="redesign")
        next_state.metadata["correction_routes"] = routes
        if skipped:
            next_state.metadata["skipped_correction_plan_ids"] = skipped
        if reevaluate:
            active_provider_id = generator_provider_id or str(
                state.metadata.get("generator_provider_id", "mock")
            )
            generated_result = run_generation(next_state, provider_id=active_provider_id)
            observe_generation(next_state, generated_result)
            run_verification(next_state, generated_result)
            after_report = run_evaluation(
                next_state,
                generated_result=generated_result,
                rubric_id=source_report.rubric_id,
            )
            score_delta = ScoreDeltaBuilder().build(source_report, after_report)
            regression_check = RegressionCheckBuilder().build(source_report, after_report, score_delta)
            physical_candidate = (
                build_report_target_evaluation(
                    next_state,
                    after_report,
                    generated_result,
                    iteration=f"v{next_state.version}",
                )
                if physical_revision_plan
                else {}
            )
            physical_gate = (
                compare_report_target_evaluations(
                    physical_source,
                    physical_candidate,
                    revision_plan=physical_revision_plan,
                )
                if physical_candidate
                else {}
            )
            if physical_gate:
                after_report.metadata["physical_convergence"] = {
                    "source": physical_source,
                    "candidate": physical_candidate,
                    "revision_plan": physical_revision_plan,
                    "candidate_gate": physical_gate,
                }
                regression_check.metadata["physical_convergence_candidate_gate"] = physical_gate
                if physical_gate["candidate_status"] == "rejected":
                    regression_check.status = "regressed"
                    regression_check.summary = (
                        regression_check.summary
                        + " Physical convergence rejected candidate: "
                        + "; ".join(physical_gate["rejection_reasons"])
                    )
            next_state.score_deltas.append(score_delta)
            next_state.regression_checks.append(regression_check)
            if next_state.version_diffs:
                next_state.version_diffs[-1].resolved_issues = regression_check.resolved_issue_ids
                next_state.version_diffs[-1].new_issues = regression_check.new_issue_ids
                next_state.version_diffs[-1].metadata["regression_status"] = regression_check.status
                if physical_gate:
                    next_state.version_diffs[-1].metadata["physical_convergence_candidate_gate"] = physical_gate
            next_state.metadata["redesign_result"].update(
                {
                    "after_evaluation_id": after_report.evaluation_id,
                    "score_delta_id": score_delta.score_delta_id,
                    "regression_check_id": regression_check.regression_check_id,
                    "overall_delta": score_delta.overall_delta,
                    "regression_status": regression_check.status,
                }
            )
            if physical_gate:
                next_state.metadata["physical_convergence"] = {
                    "revision_plan": physical_revision_plan,
                    "candidate_gate": physical_gate,
                    "accepted_version": (
                        state.version
                        if physical_gate["candidate_status"] == "rejected"
                        else next_state.version
                    ),
                    "candidate_version": next_state.version,
                }
            next_state.touch()
        return next_state


def _generated_result_for_report(state: ProjectState, report: EvaluationReport):
    return next(
        (
            item
            for item in state.generation_results
            if item.generated_result_id == report.generated_result_id
        ),
        None,
    )


def _attach_physical_plan(plans, revision_plan: dict) -> None:
    if not revision_plan:
        return
    for plan in plans:
        if plan.metadata.get("layer_id") != "physical_effect":
            continue
        plan.metadata["physical_convergence"] = {
            "revision_plan": revision_plan,
            "repair_targets": revision_plan.get("convergence_strategy", {}).get("repair_targets", []),
            "locked_targets": revision_plan.get("convergence_strategy", {}).get("locked_targets", []),
        }
