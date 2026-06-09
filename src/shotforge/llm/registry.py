from __future__ import annotations

from shotforge.config import get_settings
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
    from shotforge.llm.ollama import OllamaProvider
    from shotforge.llm.openai_compatible import OpenAICompatibleProvider
    from shotforge.llm.vllm import VLLMProvider

    settings = get_settings()
    registry = LLMRegistry()
    registry.register(MockLLMProvider(), available=True)
    openai_compatible = OpenAICompatibleProvider(settings=settings)
    registry.register(
        openai_compatible,
        available=settings.llm_provider == "openai-compatible" and openai_compatible.is_configured(),
    )
    registry.register(
        OllamaProvider(
            model=settings.llm_model if settings.llm_provider == "ollama" else "local-ollama-model",
            base_url=settings.llm_base_url or "http://localhost:11434/v1",
            api_key=settings.llm_api_key or "ollama",
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
        ),
        available=settings.llm_provider == "ollama",
    )
    registry.register(
        VLLMProvider(
            model=settings.llm_model if settings.llm_provider == "vllm" else "local-vllm-model",
            base_url=settings.llm_base_url or "http://localhost:8000/v1",
            api_key=settings.llm_api_key or "local",
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
        ),
        available=settings.llm_provider == "vllm",
    )
    return registry


def build_llm_catalog() -> LLMRegistry:
    from shotforge.llm.mock import MockLLMProvider
    from shotforge.llm.ollama import OllamaProvider
    from shotforge.llm.openai_compatible import OpenAICompatibleProvider
    from shotforge.llm.vllm import VLLMProvider

    settings = get_settings()
    registry = LLMRegistry()
    registry.register(MockLLMProvider(), available=True)
    openai_compatible = OpenAICompatibleProvider(settings=settings)
    registry.register(openai_compatible, available=openai_compatible.is_configured())
    registry.register(
        OllamaProvider(
            model=settings.llm_model if settings.llm_provider == "ollama" else "local-ollama-model",
            base_url=settings.llm_base_url or "http://localhost:11434/v1",
            api_key=settings.llm_api_key or "ollama",
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
        ),
        available=settings.llm_provider == "ollama",
    )
    registry.register(
        VLLMProvider(
            model=settings.llm_model if settings.llm_provider == "vllm" else "local-vllm-model",
            base_url=settings.llm_base_url or "http://localhost:8000/v1",
            api_key=settings.llm_api_key or "local",
            temperature=settings.llm_temperature,
            timeout_seconds=settings.llm_timeout_seconds,
        ),
        available=settings.llm_provider == "vllm",
    )
    return registry
