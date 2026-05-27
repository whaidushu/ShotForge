from __future__ import annotations

from shotforge.evaluators.base import EvaluationSignal, EvaluatorContext


class PromptStaticEvaluator:
    evaluator_id = "prompt_static"

    REQUIRED_PROMPT_MARKERS = [
        "visual style",
        "key visuals",
        "audio intent",
    ]

    def evaluate(self, context: EvaluatorContext) -> list[EvaluationSignal]:
        dimension_ids = {dimension.id for dimension in context.rubric.dimensions}
        if "prompt_executability" not in dimension_ids:
            return []

        signals = []
        for prompt in context.state.prompt_package.prompts:
            text = prompt.prompt.lower()
            missing = [marker for marker in self.REQUIRED_PROMPT_MARKERS if marker not in text]
            shot = next(item for item in context.state.shots if item.shot_id == prompt.shot_id)
            score = self._score_prompt(text=text, missing=missing, has_motion=shot.motion is not None)
            signals.append(
                EvaluationSignal(
                    signal_id=f"{self.evaluator_id}:{prompt.shot_id}:prompt_executability",
                    source=self.evaluator_id,
                    dimension_id="prompt_executability",
                    shot_id=prompt.shot_id,
                    score=score,
                    evidence=[
                        f"missing_markers={missing}" if missing else "required prompt markers present",
                        f"prompt_length={len(prompt.prompt)}",
                    ],
                    confidence=0.9,
                    metadata={
                        "required_markers": self.REQUIRED_PROMPT_MARKERS,
                        "missing_markers": missing,
                    },
                )
            )
        return signals

    def _score_prompt(self, text: str, missing: list[str], has_motion: bool) -> float:
        score = 0.88
        score -= 0.12 * len(missing)
        if len(text) < 120:
            score -= 0.1
        if not has_motion:
            score -= 0.1
        return max(0.0, min(1.0, round(score, 3)))
