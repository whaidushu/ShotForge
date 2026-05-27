from __future__ import annotations

from shotforge.llm.provider import LLMProvider


class LLMRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._availability: dict[str, bool] = {}

    def register(self, provider: LLMProvider, available: bool = True) -> None:
        self._providers[provider.model_name] = provider
        self._availability[provider.model_name] = available

    def get(self, model_name: str, require_available: bool = True) -> LLMProvider:
        provider = self._providers.get(model_name)
        if provider is None:
            available = ", ".join(self.list()) or "none"
            raise KeyError(f"Unknown LLM provider: {model_name}. Available: {available}")
        if require_available and not self.is_available(model_name):
            raise KeyError(f"LLM provider is not available yet: {model_name}")
        return provider

    def list(self, available_only: bool = True) -> list[str]:
        if available_only:
            return sorted(model_name for model_name in self._providers if self.is_available(model_name))
        return sorted(self._providers)

    def is_available(self, model_name: str) -> bool:
        return self._availability.get(model_name, False)


def build_default_llm_registry() -> LLMRegistry:
    from shotforge.llm.mock import MockLLMProvider

    registry = LLMRegistry()
    registry.register(MockLLMProvider())
    return registry


def build_llm_catalog() -> LLMRegistry:
    from shotforge.llm.mock import MockLLMProvider
    from shotforge.llm.ollama import OllamaProvider
    from shotforge.llm.vllm import VLLMProvider

    registry = LLMRegistry()
    registry.register(MockLLMProvider(), available=True)
    registry.register(OllamaProvider(), available=False)
    registry.register(VLLMProvider(), available=False)
    return registry
