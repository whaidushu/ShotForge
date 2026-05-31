from __future__ import annotations

from shotforge.config import get_settings
from shotforge.evaluators.base import EvaluatorProvider
from shotforge.evaluators.frame_consistency_evaluator import FrameConsistencyEvaluator
from shotforge.evaluators.llm_story_prompt_evaluator import LLMStoryPromptEvaluator
from shotforge.evaluators.mock_visual_evaluator import MockVisualEvaluator
from shotforge.evaluators.physical_effect_evaluator import PhysicalEffectEvaluator
from shotforge.evaluators.prompt_static_evaluator import PromptStaticEvaluator


class EvaluatorRegistry:
    def __init__(self):
        self._providers: dict[str, EvaluatorProvider] = {}

    @classmethod
    def defaults(cls) -> "EvaluatorRegistry":
        settings = get_settings()
        registry = cls()
        registry.register(PhysicalEffectEvaluator())
        registry.register(FrameConsistencyEvaluator())
        if settings.evaluator_mode in {"mock", "hybrid"}:
            registry.register(MockVisualEvaluator())
            registry.register(PromptStaticEvaluator())
        if settings.evaluator_mode in {"llm", "hybrid"}:
            registry.register(LLMStoryPromptEvaluator(provider_name=settings.llm_provider))
        return registry

    def register(self, provider: EvaluatorProvider) -> None:
        self._providers[provider.evaluator_id] = provider

    def providers(self) -> list[EvaluatorProvider]:
        return list(self._providers.values())
