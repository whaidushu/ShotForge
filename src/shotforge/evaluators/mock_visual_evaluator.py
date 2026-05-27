from __future__ import annotations

from shotforge.evaluators.base import EvaluationSignal, EvaluatorContext


class MockVisualEvaluator:
    evaluator_id = "mock_visual"

    def evaluate(self, context: EvaluatorContext) -> list[EvaluationSignal]:
        signals: list[EvaluationSignal] = []
        dimension_ids = {dimension.id for dimension in context.rubric.dimensions}
        for generated_shot in context.generated_result.shots:
            for dimension_id, score in generated_shot.quality_signals.items():
                if dimension_id not in dimension_ids:
                    continue
                signals.append(
                    EvaluationSignal(
                        signal_id=f"{self.evaluator_id}:{generated_shot.shot_id}:{dimension_id}",
                        source=self.evaluator_id,
                        dimension_id=dimension_id,
                        shot_id=generated_shot.shot_id,
                        score=score,
                        evidence=[generated_shot.observed_summary],
                        confidence=0.8,
                        metadata={
                            "mock_video_uri": generated_shot.mock_video_uri,
                            "signal_origin": "GeneratedShotResult.quality_signals",
                        },
                    )
                )
        return signals
