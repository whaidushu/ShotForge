from __future__ import annotations

from shotforge.agents.correction import build_default_correction_registry
from shotforge.agents.evaluation import CorrectionRouter
from shotforge.agents.structuring import OutputStructuringAgent
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
        plans = run_redesign_planning(state, report=source_report)
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
            next_state.score_deltas.append(score_delta)
            next_state.regression_checks.append(regression_check)
            if next_state.version_diffs:
                next_state.version_diffs[-1].resolved_issues = regression_check.resolved_issue_ids
                next_state.version_diffs[-1].new_issues = regression_check.new_issue_ids
                next_state.version_diffs[-1].metadata["regression_status"] = regression_check.status
            next_state.metadata["redesign_result"].update(
                {
                    "after_evaluation_id": after_report.evaluation_id,
                    "score_delta_id": score_delta.score_delta_id,
                    "regression_check_id": regression_check.regression_check_id,
                    "overall_delta": score_delta.overall_delta,
                    "regression_status": regression_check.status,
                }
            )
            next_state.touch()
        return next_state
