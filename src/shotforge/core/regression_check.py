from __future__ import annotations

from shotforge.core.project_state import (
    DimensionDelta,
    EvaluationReport,
    RegressionCheck,
    ScoreDelta,
)


class ScoreDeltaBuilder:
    def build(self, before: EvaluationReport, after: EvaluationReport) -> ScoreDelta:
        before_scores = {
            score.dimension_id: score for score in before.score_card.dimension_scores
        }
        after_scores = {score.dimension_id: score for score in after.score_card.dimension_scores}
        dimension_deltas: list[DimensionDelta] = []
        for dimension_id in sorted(set(before_scores) & set(after_scores)):
            before_score = before_scores[dimension_id]
            after_score = after_scores[dimension_id]
            dimension_deltas.append(
                DimensionDelta(
                    dimension_id=dimension_id,
                    label=after_score.label,
                    before_score=before_score.score,
                    after_score=after_score.score,
                    delta=round(after_score.score - before_score.score, 3),
                )
            )
        return ScoreDelta(
            from_version=before.version_id,
            to_version=after.version_id,
            before_evaluation_id=before.evaluation_id,
            after_evaluation_id=after.evaluation_id,
            overall_before=before.score_card.overall_score,
            overall_after=after.score_card.overall_score,
            overall_delta=round(after.score_card.overall_score - before.score_card.overall_score, 3),
            dimension_deltas=dimension_deltas,
            metadata={
                "improved_dimensions": [
                    item.dimension_id for item in dimension_deltas if item.delta > 0
                ],
                "regressed_dimensions": [
                    item.dimension_id for item in dimension_deltas if item.delta < 0
                ],
            },
        )


class RegressionCheckBuilder:
    def build(
        self,
        before: EvaluationReport,
        after: EvaluationReport,
        score_delta: ScoreDelta,
    ) -> RegressionCheck:
        before_keys = {self._issue_key(issue): issue.issue_id for issue in before.issues}
        after_keys = {self._issue_key(issue): issue.issue_id for issue in after.issues}
        resolved_keys = sorted(set(before_keys) - set(after_keys))
        remaining_keys = sorted(set(before_keys) & set(after_keys))
        new_keys = sorted(set(after_keys) - set(before_keys))
        status = self._status(score_delta.overall_delta, resolved_keys, new_keys)
        return RegressionCheck(
            from_version=before.version_id,
            to_version=after.version_id,
            resolved_issue_ids=[before_keys[key] for key in resolved_keys],
            remaining_issue_ids=[after_keys[key] for key in remaining_keys],
            new_issue_ids=[after_keys[key] for key in new_keys],
            status=status,
            summary=self._summary(status, score_delta.overall_delta, resolved_keys, new_keys),
            metadata={
                "resolved_issue_keys": resolved_keys,
                "remaining_issue_keys": remaining_keys,
                "new_issue_keys": new_keys,
            },
        )

    def _issue_key(self, issue) -> str:
        return f"{issue.dimension_id}:{issue.shot_id or 'project'}"

    def _status(self, overall_delta: float, resolved: list[str], new: list[str]) -> str:
        if overall_delta > 0 and resolved and not new:
            return "improved"
        if overall_delta < 0 or len(new) > len(resolved):
            return "regressed"
        if overall_delta == 0 and not resolved and not new:
            return "unchanged"
        return "mixed"

    def _summary(
        self,
        status: str,
        overall_delta: float,
        resolved: list[str],
        new: list[str],
    ) -> str:
        return (
            f"{status}: overall delta {overall_delta:+.3f}, "
            f"resolved {len(resolved)}, new {len(new)}."
        )
