from __future__ import annotations

from collections import defaultdict

from shotforge.core.project_state import (
    CorrectionPlan,
    EvaluationReport,
    Issue,
    ProjectState,
    RedesignPlan,
)
from shotforge.core.trace_log import TraceLog
from shotforge.i18n import get_translator


class SuggestionAgent:
    def plan(self, state: ProjectState, report: EvaluationReport | None = None) -> list[CorrectionPlan]:
        with TraceLog(state).span("suggestion_agent"):
            target_report = report or state.evaluation_reports[-1]
            redesign_plan = self._redesign_plan(target_report)
            active_issue_ids = set(redesign_plan.fix_issue_ids)
            active_issues = [
                issue for issue in target_report.issues if issue.issue_id in active_issue_ids
            ]
            grouped = self._group_issues(active_issues)
            plans = [
                self._plan_for_group(state.language, target_report.evaluation_id, correction_type, issues)
                for correction_type, issues in grouped.items()
            ]
            plans.sort(key=lambda item: item.priority)
            state.redesign_plans.append(redesign_plan)
            state.correction_plans.extend(plans)
            state.touch()
            return plans

    def _group_issues(self, issues: list[Issue]) -> dict[str, list[Issue]]:
        grouped: dict[str, list[Issue]] = defaultdict(list)
        for issue in issues:
            grouped[issue.correction_type].append(issue)
        return grouped

    def _plan_for_group(
        self,
        language: str,
        evaluation_id: str,
        correction_type: str,
        issues: list[Issue],
    ) -> CorrectionPlan:
        shot_ids = sorted({issue.shot_id for issue in issues if issue.shot_id})
        prompt_fields = self._prompt_fields(issues)
        affected_fields = self._affected_fields(correction_type, shot_ids, prompt_fields)
        layer_index = self._layer_index(issues)
        layer_id = self._layer_id(issues)
        return CorrectionPlan(
            source_evaluation_id=evaluation_id,
            target_issue_ids=[issue.issue_id for issue in issues],
            correction_strategy=self._strategy(language, correction_type, issues),
            selected_agent=f"{correction_type}_correction_agent",
            affected_fields=affected_fields,
            expected_improvement={
                issue.dimension_id: round(1 - float(issue.metadata.get("score", 0.7)), 3)
                for issue in issues
            },
            risk=self._risk(language, correction_type),
            priority=self._priority(issues),
            metadata={
                "correction_type": correction_type,
                "shot_ids": shot_ids,
                "issue_count": len(issues),
                "layer_id": layer_id,
                "layer_index": layer_index,
                "prompt_fields": prompt_fields,
            },
        )

    def _affected_fields(
        self,
        correction_type: str,
        shot_ids: list[str],
        prompt_fields: list[str],
    ) -> list[str]:
        fields = []
        for shot_id in shot_ids:
            if correction_type in {"action", "emotion", "scene", "camera"}:
                fields.append(f"shots[{shot_id}]")
                fields.append(f"prompt_package.prompts[{shot_id}]")
            if correction_type == "audio":
                fields.append(f"audio_cues[{shot_id}]")
                fields.append(f"prompt_package.prompts[{shot_id}]")
            if correction_type == "prompt":
                fields.append(f"prompt_package.prompts[{shot_id}]")
            if correction_type == "character":
                fields.append("characters")
                fields.append(f"prompt_package.prompts[{shot_id}]")
            for prompt_field in prompt_fields:
                fields.append(f"prompt_package.prompts[{shot_id}].structured_template.{prompt_field}")
        return sorted(set(fields))

    def _strategy(self, language: str, correction_type: str, issues: list[Issue]) -> str:
        labels = ", ".join(sorted({issue.dimension_label for issue in issues}))
        translator = get_translator()
        correction_label = translator.t(
            language,
            f"agents.suggestion.correction_type_labels.{correction_type}",
        )
        return translator.t(
            language,
            "agents.suggestion.strategy",
            dimensions=labels,
            correction_type=correction_label,
        )

    def _risk(self, language: str, correction_type: str) -> str:
        translator = get_translator()
        risk = translator.t(language, f"agents.suggestion.risks.{correction_type}")
        if risk == f"agents.suggestion.risks.{correction_type}":
            return translator.t(language, "agents.suggestion.risks.default")
        return risk

    def _priority(self, issues: list[Issue]) -> int:
        severity_rank = {"critical": 0, "high": 10, "medium": 30, "low": 60}
        layer_index = self._layer_index(issues)
        severity = min(severity_rank.get(issue.severity, 100) for issue in issues)
        return layer_index * 100 + severity

    def _redesign_plan(self, report: EvaluationReport) -> RedesignPlan:
        ordered_issues = sorted(report.issues, key=lambda issue: self._layer_index([issue]))
        if not ordered_issues:
            return RedesignPlan(
                source_evaluation_id=report.evaluation_id,
                target_layer_id="none",
                target_layer_index=99,
                rationale="No issues found; no redesign required.",
            )
        target_layer_index = self._layer_index([ordered_issues[0]])
        target_layer_id = self._layer_id([ordered_issues[0]])
        fix_issues = [
            issue for issue in ordered_issues if self._layer_index([issue]) == target_layer_index
        ]
        deferred = [
            issue for issue in ordered_issues if self._layer_index([issue]) > target_layer_index
        ]
        return RedesignPlan(
            source_evaluation_id=report.evaluation_id,
            target_layer_id=target_layer_id,
            target_layer_index=target_layer_index,
            fix_issue_ids=[issue.issue_id for issue in fix_issues],
            protect_fields=self._prompt_fields(deferred),
            defer_issue_ids=[issue.issue_id for issue in deferred],
            rationale=(
                f"Prioritize layer {target_layer_index} ({target_layer_id}) before higher-layer optimization."
            ),
            metadata={
                "fix_issue_count": len(fix_issues),
                "defer_issue_count": len(deferred),
                "layer_policy": "lowest-layer-first",
            },
        )

    def _layer_index(self, issues: list[Issue]) -> int:
        return min(int(issue.metadata.get("layer_index", 99)) for issue in issues)

    def _layer_id(self, issues: list[Issue]) -> str:
        return str(min(issues, key=lambda issue: int(issue.metadata.get("layer_index", 99))).metadata.get("layer_id", "creative_quality"))

    def _prompt_fields(self, issues: list[Issue]) -> list[str]:
        fields = {
            str(field)
            for issue in issues
            for field in issue.metadata.get("prompt_fields", [])
        }
        return sorted(fields)
