from __future__ import annotations

from statistics import mean

from shotforge.evaluators.base import EvaluationSignal


class SignalAggregator:
    def aggregate_dimension_score(self, signals: list[EvaluationSignal], dimension_id: str) -> float:
        values = [signal.score for signal in signals if signal.dimension_id == dimension_id]
        return round(mean(values), 3) if values else 0.7

    def weak_shot_signals(
        self,
        signals: list[EvaluationSignal],
        dimension_id: str,
        threshold: float,
    ) -> list[EvaluationSignal]:
        return [
            signal
            for signal in signals
            if signal.dimension_id == dimension_id
            and signal.shot_id is not None
            and signal.score < threshold
        ]

    def evidence_for(self, signals: list[EvaluationSignal]) -> str:
        evidence = []
        for signal in signals:
            evidence.extend(signal.evidence)
        return " | ".join(evidence[:4])
