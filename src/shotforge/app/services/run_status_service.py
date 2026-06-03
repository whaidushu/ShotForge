from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shotforge.app.services.run_job_service import (
    completed_steps_for_state,
    expected_steps_for_mode,
)
from shotforge.config import get_settings
from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.project_state import ProjectState


LIFECYCLE_STAGES = [
    {"id": "draft"},
    {"id": "designed"},
    {"id": "generated"},
    {"id": "observed"},
    {"id": "evaluated"},
    {"id": "needs_revision"},
    {"id": "revised"},
    {"id": "ready_for_handoff"},
    {"id": "blocked"},
]

STAGE_INDEX = {stage["id"]: index for index, stage in enumerate(LIFECYCLE_STAGES)}


class RunSummary(BaseModel):
    run_id: str
    project_id: str
    idea: str
    mode: str
    version: int
    lifecycle_stage: str
    lifecycle_label: str
    lifecycle_index: int
    readiness_score: int
    readiness_status: str
    next_action: str
    latest_score: float | None = None
    issue_count: int = 0
    high_issue_count: int = 0
    artifact_count: int = 0
    export_count: int = 0
    version_count: int = 1
    provider_status: str = "unknown"
    harness_evidence_count: int = 0
    generator_provider_id: str = ""
    provider_profile_name: str = ""
    updated_at: float = 0
    blockers: list[str] = Field(default_factory=list)


class RunDashboard(BaseModel):
    total_runs: int = 0
    ready_for_handoff: int = 0
    needs_revision: int = 0
    blocked: int = 0
    average_readiness_score: int = 0
    runs: list[RunSummary] = Field(default_factory=list)


class RunWorkbench(BaseModel):
    summary: RunSummary | None = None
    lifecycle: list[dict[str, Any]] = Field(default_factory=list)
    overview_metrics: list[dict[str, Any]] = Field(default_factory=list)
    iteration_timeline: list[dict[str, Any]] = Field(default_factory=list)
    handoff_center: dict[str, Any] = Field(default_factory=dict)
    harness_evidence: dict[str, Any] = Field(default_factory=dict)
    next_actions: list[str] = Field(default_factory=list)


class RunStatusService:
    def dashboard(self, limit: int = 40) -> RunDashboard:
        summaries: list[RunSummary] = []
        for state, package_path in self._load_recent_states(limit=limit):
            summaries.append(self.summary(state, updated_at=package_path.stat().st_mtime))

        total = len(summaries)
        readiness_scores = [item.readiness_score for item in summaries]
        return RunDashboard(
            total_runs=total,
            ready_for_handoff=len(
                [item for item in summaries if item.lifecycle_stage == "ready_for_handoff"]
            ),
            needs_revision=len(
                [item for item in summaries if item.lifecycle_stage == "needs_revision"]
            ),
            blocked=len([item for item in summaries if item.lifecycle_stage == "blocked"]),
            average_readiness_score=round(sum(readiness_scores) / total) if total else 0,
            runs=summaries,
        )

    def workbench(self, state: ProjectState | None) -> RunWorkbench:
        if state is None:
            return RunWorkbench()

        summary = self.summary(state)
        return RunWorkbench(
            summary=summary,
            lifecycle=self.lifecycle_steps(summary.lifecycle_stage),
            overview_metrics=self.overview_metrics(state, summary),
            iteration_timeline=self.iteration_timeline(state),
            handoff_center=self.handoff_center(state),
            harness_evidence=self.harness_evidence(state),
            next_actions=self.next_actions(state, summary.lifecycle_stage),
        )

    def summary(self, state: ProjectState, *, updated_at: float = 0) -> RunSummary:
        latest_report = state.evaluation_reports[-1] if state.evaluation_reports else None
        latest_score = latest_report.score_card.overall_score if latest_report else None
        issues = latest_report.issues if latest_report else []
        high_issue_count = len(
            [issue for issue in issues if issue.severity in {"high", "critical"}]
        )
        readiness_status, blockers = self.readiness_status(state, high_issue_count)
        lifecycle_stage = self.lifecycle_stage(state, readiness_status, high_issue_count)
        harness_audit = build_harness_audit(state)
        return RunSummary(
            run_id=state.run_id,
            project_id=state.project_id,
            idea=state.user_idea,
            mode=str(state.metadata.get("run_mode", "design")),
            version=state.version,
            lifecycle_stage=lifecycle_stage,
            lifecycle_label=lifecycle_stage,
            lifecycle_index=STAGE_INDEX.get(lifecycle_stage, 0),
            readiness_score=self.readiness_score(state, latest_score, readiness_status),
            readiness_status=readiness_status,
            next_action=self.next_action_for_stage(lifecycle_stage),
            latest_score=latest_score,
            issue_count=len(issues),
            high_issue_count=high_issue_count,
            artifact_count=sum(len(result.shots) for result in state.generation_results),
            export_count=len(state.exports),
            version_count=max(state.version, len(state.version_diffs) + 1),
            provider_status=self.provider_status(state, blockers),
            harness_evidence_count=sum(
                int(harness_audit["state_summary"].get(key, 0) or 0)
                for key in [
                    "tool_calls",
                    "tool_orchestration",
                    "memory_selections",
                    "sandbox_policy_records",
                    "mcp_access_records",
                    "state_transitions",
                    "agent_contracts",
                    "workflow_decisions",
                ]
            ),
            generator_provider_id=str(
                state.metadata.get("generator_provider_id", state.prompt_package.provider)
            ),
            provider_profile_name=str(state.metadata.get("provider_profile_name", "")),
            updated_at=updated_at,
            blockers=blockers,
        )

    def lifecycle_steps(self, current_stage: str) -> list[dict[str, Any]]:
        current_index = STAGE_INDEX.get(current_stage, 0)
        return [
            {
                "id": stage["id"],
                "label": stage["id"],
                "done": index < current_index and current_stage != "blocked",
                "current": stage["id"] == current_stage,
            }
            for index, stage in enumerate(LIFECYCLE_STAGES)
            if stage["id"] != "blocked" or current_stage == "blocked"
        ]

    def overview_metrics(self, state: ProjectState, summary: RunSummary) -> list[dict[str, Any]]:
        completed_steps = completed_steps_for_state(state)
        expected_steps = expected_steps_for_mode(summary.mode)
        pipeline_percent = round(len(completed_steps) / len(expected_steps) * 100)
        return [
            {"label_key": "lifecycle", "value": summary.lifecycle_stage, "value_type": "stage"},
            {"label_key": "readiness", "value": summary.readiness_score, "value_type": "percent"},
            {
                "label_key": "evaluation",
                "value": summary.latest_score,
                "value_type": "score",
            },
            {"label_key": "open_issues", "value": summary.issue_count, "value_type": "number"},
            {"label_key": "artifacts", "value": summary.artifact_count, "value_type": "number"},
            {"label_key": "exports", "value": summary.export_count, "value_type": "number"},
            {"label_key": "provider", "value": summary.generator_provider_id, "value_type": "text"},
            {
                "label_key": "provider_status",
                "value": summary.provider_status,
                "value_type": "provider_status",
            },
            {"label_key": "pipeline", "value": pipeline_percent, "value_type": "percent"},
            {
                "label_key": "harness_records",
                "value": summary.harness_evidence_count,
                "value_type": "number",
            },
        ]

    def iteration_timeline(self, state: ProjectState) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = [
            {
                "version": "v1",
                "title_key": "initial_title",
                "status": "designed",
                "score": self._score_for_version(state, 1),
                "summary_key": "initial_summary",
                "issue_count": self._issue_count_for_version(state, 1),
            }
        ]
        for diff in state.version_diffs:
            regression = next(
                (item for item in state.regression_checks if item.to_version == diff.to_version),
                None,
            )
            score_delta = next(
                (item for item in state.score_deltas if item.to_version == diff.to_version),
                None,
            )
            timeline.append(
                {
                    "version": f"v{diff.to_version}",
                    "title_key": "revision_title",
                    "from_version": diff.from_version,
                    "to_version": diff.to_version,
                    "status": regression.status if regression else "revised",
                    "score": self._score_for_version(state, diff.to_version),
                    "delta": score_delta.overall_delta if score_delta else None,
                    "summary": diff.explanation,
                    "summary_key": "" if diff.explanation else "diff_recorded",
                    "changed_shots": diff.changed_shots,
                    "changed_prompts": diff.changed_prompts,
                    "resolved_issues": diff.resolved_issues,
                    "issue_count": self._issue_count_for_version(state, diff.to_version),
                }
            )
        return timeline

    def handoff_center(self, state: ProjectState) -> dict[str, Any]:
        exports = [
            {
                "format": item.format,
                "label_key": item.format,
                "url": f"/api/runs/{state.run_id}/export/{item.format}",
                "path": item.path,
            }
            for item in state.exports
        ]
        readiness = state.delivery_readiness
        return {
            "overall_status": readiness.overall_status if readiness else "not_started",
            "deliverables": [self._public_deliverable_label(item) for item in readiness.handoff_deliverables]
            if readiness
            else [],
            "next_actions": self.next_actions(
                state, self.lifecycle_stage(state, "warning" if readiness else "not_started", 0)
            ),
            "risks": readiness.risk_register if readiness else [],
            "checks": [item.model_dump(mode="json") for item in readiness.checks]
            if readiness
            else [],
            "exports": exports,
        }

    def harness_evidence(self, state: ProjectState) -> dict[str, Any]:
        audit = build_harness_audit(state)
        latest_context = audit.get("latest_context", {})
        return {
            "counts": audit.get("state_summary", {}),
            "agent_topology": audit.get("agent_topology", {"nodes": [], "edges": []}),
            "latest_context": latest_context,
            "connected_tools": latest_context.get("mcp_tool_names", []),
            "memory": latest_context.get("memory", {}),
            "sandbox_policy": latest_context.get("sandbox_policy", {}),
            "tool_calls": audit.get("tool_calls", [])[-6:],
            "state_transitions": audit.get("state_transitions", [])[-6:],
            "workflow_decisions": audit.get("workflow_decisions", [])[-6:],
        }

    def readiness_status(
        self, state: ProjectState, high_issue_count: int
    ) -> tuple[str, list[str]]:
        blockers: list[str] = []
        readiness = state.delivery_readiness
        if readiness:
            failed_checks = [item for item in readiness.checks if item.status == "failed"]
            warning_checks = [item for item in readiness.checks if item.status == "warning"]
            if failed_checks:
                blockers.extend(item.check_id for item in failed_checks)
                return "failed", blockers
            if warning_checks:
                blockers.extend(item.check_id for item in warning_checks)
                return "warning", blockers
            if readiness.overall_status == "failed":
                blockers.append("delivery_readiness")
                return "failed", blockers
            if readiness.overall_status == "warning":
                blockers.append("delivery_readiness")
                return "warning", blockers
        if any(decision.decision == "block" for decision in state.workflow_decisions):
            blockers.append("workflow_decision")
            return "failed", blockers
        if high_issue_count:
            blockers.append("high_priority_issues")
            return "needs_revision", blockers
        if readiness:
            return readiness.overall_status, blockers
        if state.exports:
            return "warning", blockers
        return "not_started", blockers

    def lifecycle_stage(
        self,
        state: ProjectState,
        readiness_status: str,
        high_issue_count: int,
    ) -> str:
        if readiness_status == "failed":
            return "blocked"
        if readiness_status in {"warning", "needs_revision"} or high_issue_count > 0:
            return "needs_revision"
        if state.delivery_readiness and readiness_status == "passed" and state.exports:
            return "ready_for_handoff"
        if state.convergence_steps or state.version > 1:
            return "revised"
        if state.evaluation_reports:
            return "evaluated"
        if state.observation_reports:
            return "observed"
        if state.generation_results:
            return "generated"
        if state.shots or state.prompt_package.prompts:
            return "designed"
        return "draft"

    def readiness_score(
        self,
        state: ProjectState,
        latest_score: float | None,
        readiness_status: str,
    ) -> int:
        mode = str(state.metadata.get("run_mode", "design"))
        expected_steps = expected_steps_for_mode(mode)
        pipeline_ratio = len(completed_steps_for_state(state)) / len(expected_steps)
        export_ratio = min(len(state.exports) / 6, 1)
        if state.delivery_readiness and state.delivery_readiness.checks:
            checks = state.delivery_readiness.checks
            readiness_ratio = len([item for item in checks if item.status == "passed"]) / len(checks)
        else:
            readiness_ratio = 0.5 if state.exports else 0
        score_ratio = latest_score if latest_score is not None else pipeline_ratio
        raw_score = (
            pipeline_ratio * 0.35
            + readiness_ratio * 0.25
            + score_ratio * 0.25
            + export_ratio * 0.15
        )
        if readiness_status == "failed":
            raw_score = min(raw_score, 0.49)
        if readiness_status == "needs_revision":
            raw_score = min(raw_score, 0.72)
        return max(0, min(round(raw_score * 100), 100))

    def next_actions(self, state: ProjectState, lifecycle_stage: str) -> list[str]:
        decision_actions = [
            action
            for decision in reversed(state.workflow_decisions)
            for action in decision.required_actions
        ]
        if decision_actions:
            return decision_actions[:3]
        readiness = state.delivery_readiness
        if readiness and readiness.next_actions:
            return readiness.next_actions
        return [self.next_action_for_stage(lifecycle_stage)]

    def next_action_for_stage(self, lifecycle_stage: str) -> str:
        return {
            "draft": "draft",
            "designed": "designed",
            "generated": "generated",
            "observed": "observed",
            "evaluated": "evaluated",
            "needs_revision": "needs_revision",
            "revised": "revised",
            "ready_for_handoff": "ready_for_handoff",
            "blocked": "blocked",
        }.get(lifecycle_stage, "review")

    def provider_status(self, state: ProjectState, blockers: list[str]) -> str:
        if any("provider" in item or "workflow" in item for item in blockers):
            return "attention"
        if state.metadata.get("generator_provider_id") or state.metadata.get("llm_provider_id"):
            return "configured"
        return "unknown"

    def _load_recent_states(self, *, limit: int) -> list[tuple[ProjectState, Path]]:
        runs_dir = get_settings().runs_dir
        if not runs_dir.exists():
            return []
        package_paths = sorted(
            runs_dir.glob("*/package.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        states: list[tuple[ProjectState, Path]] = []
        for path in package_paths[:limit]:
            try:
                states.append(
                    (ProjectState.model_validate_json(path.read_text(encoding="utf-8")), path)
                )
            except Exception:
                continue
        return states

    def _score_for_version(self, state: ProjectState, version: int) -> float | None:
        report = next(
            (item for item in reversed(state.evaluation_reports) if item.target_version == version),
            None,
        )
        return report.score_card.overall_score if report else None

    def _issue_count_for_version(self, state: ProjectState, version: int) -> int:
        report = next(
            (item for item in reversed(state.evaluation_reports) if item.target_version == version),
            None,
        )
        return len(report.issues) if report else 0

    @staticmethod
    def _public_deliverable_label(label: str) -> str:
        return label.replace("Harness Inspector", "Harness evidence")


__all__ = ["RunDashboard", "RunStatusService", "RunSummary", "RunWorkbench"]
