from __future__ import annotations

from shotforge.generators.base import GeneratorProvider


class GeneratorRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, GeneratorProvider] = {}
        self._availability: dict[str, bool] = {}

    def register(self, provider: GeneratorProvider, available: bool = True) -> None:
        self._providers[provider.provider_id] = provider
        self._availability[provider.provider_id] = available

    def get(self, provider_id: str, require_available: bool = True) -> GeneratorProvider:
        provider = self._providers.get(provider_id)
        if provider is None:
            available = ", ".join(self.list()) or "none"
            raise KeyError(f"Unknown generator provider: {provider_id}. Available: {available}")
        if require_available and not self.is_available(provider_id):
            raise KeyError(f"Generator provider is not available yet: {provider_id}")
        return provider

    def list(self, available_only: bool = True) -> list[str]:
        if available_only:
            return sorted(provider_id for provider_id in self._providers if self.is_available(provider_id))
        return sorted(self._providers)

    def is_available(self, provider_id: str) -> bool:
        return self._availability.get(provider_id, False)


def build_default_generator_registry() -> GeneratorRegistry:
    from shotforge.config import get_settings
    from shotforge.generators.comfyui_provider import ComfyUIProvider
    from shotforge.generators.mock_generator import MockGenerator

    settings = get_settings()
    registry = GeneratorRegistry()
    registry.register(MockGenerator())
    if settings.comfyui_enabled:
        registry.register(ComfyUIProvider(), available=True)
    return registry


def build_generator_catalog() -> GeneratorRegistry:
    from shotforge.generators.comfyui_provider import ComfyUIProvider
    from shotforge.generators.jimeng_provider import JimengProvider
    from shotforge.generators.kling_provider import KlingProvider
    from shotforge.generators.mock_generator import MockGenerator
    from shotforge.generators.open_sora_provider import OpenSoraProvider
    from shotforge.generators.runway_provider import RunwayProvider

    from shotforge.config import get_settings

    settings = get_settings()
    registry = GeneratorRegistry()
    registry.register(MockGenerator(), available=True)
    registry.register(ComfyUIProvider(), available=settings.comfyui_enabled)
    registry.register(OpenSoraProvider(), available=False)
    registry.register(KlingProvider(), available=False)
    registry.register(JimengProvider(), available=False)
    registry.register(RunwayProvider(), available=False)
    return registry
