from __future__ import annotations

from shotforge.evaluators.base import EvaluatorProvider
from shotforge.evaluators.mock_visual_evaluator import MockVisualEvaluator
from shotforge.evaluators.prompt_static_evaluator import PromptStaticEvaluator


class EvaluatorRegistry:
    def __init__(self):
        self._providers: dict[str, EvaluatorProvider] = {}

    @classmethod
    def defaults(cls) -> "EvaluatorRegistry":
        registry = cls()
        registry.register(MockVisualEvaluator())
        registry.register(PromptStaticEvaluator())
        return registry

    def register(self, provider: EvaluatorProvider) -> None:
        self._providers[provider.evaluator_id] = provider

    def providers(self) -> list[EvaluatorProvider]:
        return list(self._providers.values())
