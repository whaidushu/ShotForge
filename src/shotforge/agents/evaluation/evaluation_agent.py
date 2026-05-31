from __future__ import annotations

from shotforge.core.project_state import (
    DimensionScore,
    EvaluationReport,
    GeneratedResult,
    Issue,
    IssueSeverity,
    ProjectState,
    ScoreCard,
)
from shotforge.core.rubrics import RubricRegistry
from shotforge.core.schemas.evaluation import EvaluationDimensionConfig, EvaluationRubric
from shotforge.core.trace_log import TraceLog
from shotforge.evaluators import EvaluationSignal, EvaluatorContext, EvaluatorRegistry, SignalAggregator


class EvaluationAgent:
    def __init__(
        self,
        rubric_registry: RubricRegistry | None = None,
        evaluator_registry: EvaluatorRegistry | None = None,
        signal_aggregator: SignalAggregator | None = None,
    ):
        self.rubric_registry = rubric_registry or RubricRegistry()
        self.evaluator_registry = evaluator_registry or EvaluatorRegistry.defaults()
        self.signal_aggregator = signal_aggregator or SignalAggregator()

    def evaluate(
        self,
        state: ProjectState,
        generated_result: GeneratedResult | None = None,
        rubric_id: str = "baseline_v1",
    ) -> EvaluationReport:
        with TraceLog(state).span("evaluation_agent", rubric_id=rubric_id):
            result = generated_result or state.generation_results[-1]
            rubric = self.rubric_registry.load(rubric_id)
            signals = self._collect_signals(state, result, rubric)
            dimension_scores = [
                self._score_dimension(state, signals, dimension)
                for dimension in rubric.dimensions
            ]
            overall = self._weighted_average(dimension_scores)
            issues = [
                issue
                for dimension, score in zip(rubric.dimensions, dimension_scores, strict=True)
                for issue in self._issues_for_dimension(state, result, signals, dimension, score.score)
            ]
            layer_summaries = self._layer_summaries(state, rubric, dimension_scores, issues)
            report = EvaluationReport(
                version_id=state.version,
                target_version=state.version,
                generated_result_id=result.generated_result_id,
                score_card=ScoreCard(
                    overall_score=overall,
                    dimension_scores=dimension_scores,
                    metadata={
                        "rubric_dimension_count": len(rubric.dimensions),
                        "rubric_layer_count": len(rubric.layers),
                        "layers": layer_summaries,
                    },
                ),
                issues=issues,
                strengths=self._strengths(dimension_scores),
                suggested_focus=self._suggested_focus(issues),
                rubric_id=rubric.id,
                metadata={
                    "rubric_version": rubric.version,
                    "extension_note": "Evaluation layers and dimensions are loaded from knowledge/evaluation_rubrics.json.",
                    "evaluator_sources": sorted({signal.source for signal in signals}),
                    "signal_count": len(signals),
                    "layer_count": len(layer_summaries),
                },
            )
            state.evaluation_reports.append(report)
            state.issue_history.extend(issues)
            state.touch()
            return report

    def _score_dimension(
        self,
        state: ProjectState,
        signals: list[EvaluationSignal],
        dimension: EvaluationDimensionConfig,
    ) -> DimensionScore:
        score = self.signal_aggregator.aggregate_dimension_score(signals, dimension.id)
        weak_signals = self.signal_aggregator.weak_shot_signals(
            signals,
            dimension.id,
            dimension.issue_rule.threshold,
        )
        related = [
            signal.shot_id
            for signal in weak_signals
            if signal.shot_id is not None
        ]
        label = dimension.label(state.language)
        signal_count = len([signal for signal in signals if signal.dimension_id == dimension.id])
        rationale = (
            f"{label} 基于 {signal_count} 个评测信号计算。"
            if state.language == "zh"
            else f"{label} is computed from {signal_count} evaluator signals."
        )
        return DimensionScore(
            dimension_id=dimension.id,
            label=label,
            score=score,
            weight=dimension.weight,
            rationale=rationale,
            related_shot_ids=related,
            metadata={
                "target": dimension.target,
                "signal_key": dimension.signal_key or dimension.id,
                "strategy": dimension.strategy,
                "dimension_metadata": dimension.metadata,
                **self._layer_metadata(dimension),
            },
        )

    def _issues_for_dimension(
        self,
        state: ProjectState,
        result: GeneratedResult,
        signals: list[EvaluationSignal],
        dimension: EvaluationDimensionConfig,
        dimension_score: float,
    ) -> list[Issue]:
        issues = []
        weak_signals = self.signal_aggregator.weak_shot_signals(
            signals,
            dimension.id,
            dimension.issue_rule.threshold,
        )
        for signal in weak_signals:
            shot_score = signal.score
            shot_id = signal.shot_id or "project"
            generated_shot = next((shot for shot in result.shots if shot.shot_id == signal.shot_id), None)
            issues.append(
                Issue(
                    severity=self._severity(shot_score, dimension.issue_rule.severity_bands),
                    dimension_id=dimension.id,
                    dimension_label=dimension.label(state.language),
                    shot_id=signal.shot_id,
                    description=self._issue_description(state, dimension, shot_id),
                    evidence=self._issue_evidence(signal, generated_shot),
                    suspected_cause=self._issue_cause(state, dimension, shot_id),
                    correction_type=dimension.issue_rule.correction_type,
                    metadata={
                        "score": shot_score,
                        "dimension_score": dimension_score,
                        "threshold": dimension.issue_rule.threshold,
                        "generated_result_id": result.generated_result_id,
                        "signal_id": signal.signal_id,
                        "signal_source": signal.source,
                        **self._layer_metadata(dimension),
                    },
                )
            )
        return issues

    def _collect_signals(
        self,
        state: ProjectState,
        result: GeneratedResult,
        rubric: EvaluationRubric,
    ) -> list[EvaluationSignal]:
        context = EvaluatorContext(state=state, generated_result=result, rubric=rubric)
        signals: list[EvaluationSignal] = []
        for provider in self.evaluator_registry.providers():
            signals.extend(provider.evaluate(context))
        return signals

    def _layer_metadata(self, dimension: EvaluationDimensionConfig) -> dict:
        return {
            "layer_id": dimension.layer_id,
            "layer_index": dimension.layer_index,
            "dimension_strategy": dimension.strategy,
            "prompt_fields": dimension.prompt_fields,
            "hard_target": dimension.hard_target,
        }

    def _layer_summaries(
        self,
        state: ProjectState,
        rubric: EvaluationRubric,
        dimension_scores: list[DimensionScore],
        issues: list[Issue],
    ) -> list[dict]:
        score_by_dimension = {score.dimension_id: score for score in dimension_scores}
        layer_by_id = {layer.id: layer for layer in rubric.layers}
        layer_ids = {dimension.layer_id for dimension in rubric.dimensions}
        summaries = []
        for layer_id in sorted(
            layer_ids,
            key=lambda item: layer_by_id[item].index if item in layer_by_id else 99,
        ):
            dimensions = [dimension for dimension in rubric.dimensions if dimension.layer_id == layer_id]
            scores = [
                score_by_dimension[dimension.id]
                for dimension in dimensions
                if dimension.id in score_by_dimension
            ]
            layer = layer_by_id.get(layer_id)
            layer_index = layer.index if layer else min(dimension.layer_index for dimension in dimensions)
            average_score = (
                round(sum(score.score for score in scores) / len(scores), 3)
                if scores
                else 0.0
            )
            summaries.append(
                {
                    "layer_id": layer_id,
                    "layer_index": layer_index,
                    "label": layer.label(state.language) if layer else layer_id,
                    "dimension_ids": [dimension.id for dimension in dimensions],
                    "average_score": average_score,
                    "issue_count": sum(
                        1 for issue in issues if issue.metadata.get("layer_id") == layer_id
                    ),
                    "objective": layer.objective if layer else "",
                    "strategy": layer.strategy if layer else "",
                    "convergence_policy": layer.convergence_policy if layer else "",
                    "metadata": layer.metadata if layer else {},
                }
            )
        return summaries

    def _issue_evidence(self, signal: EvaluationSignal, generated_shot) -> str:
        evidence = list(signal.evidence)
        if generated_shot is not None:
            evidence.insert(0, generated_shot.observed_summary)
        evidence.append(f"score={signal.score:.2f}")
        evidence.append(f"source={signal.source}")
        return " | ".join(evidence)

    def _issue_description(
        self,
        state: ProjectState,
        dimension: EvaluationDimensionConfig,
        shot_id: str,
    ) -> str:
        template = dimension.issue_rule.description(state.language)
        if state.language == "en" and template == dimension.issue_rule.description_template:
            template = "{shot_id} underperforms on " + dimension.label("en") + "."
        return template.format(shot_id=shot_id)

    def _issue_cause(
        self,
        state: ProjectState,
        dimension: EvaluationDimensionConfig,
        shot_id: str,
    ) -> str:
        template = dimension.issue_rule.cause(state.language)
        if state.language == "en" and template == dimension.issue_rule.cause_template:
            template = "The current design lacks enough concrete constraints for this dimension."
        return template.format(shot_id=shot_id)

    def _weighted_average(self, scores: list[DimensionScore]) -> float:
        total_weight = sum(score.weight for score in scores) or 1
        return round(sum(score.score * score.weight for score in scores) / total_weight, 3)

    def _severity(self, score: float, bands: dict[str, float]) -> IssueSeverity:
        if score <= bands.get("critical", 0.35):
            return "critical"
        if score <= bands.get("high", 0.5):
            return "high"
        if score <= bands.get("medium", 0.72):
            return "medium"
        return "low"

    def _strengths(self, scores: list[DimensionScore]) -> list[str]:
        return [
            f"{score.label}: {score.score:.2f}"
            for score in sorted(scores, key=lambda item: item.score, reverse=True)[:3]
        ]

    def _suggested_focus(self, issues: list[Issue]) -> list[str]:
        seen = []
        for issue in issues:
            layer = issue.metadata.get("layer_id", "unknown_layer")
            focus = f"{layer}:{issue.correction_type}:{issue.dimension_label}"
            if focus not in seen:
                seen.append(focus)
        return seen[:5]
