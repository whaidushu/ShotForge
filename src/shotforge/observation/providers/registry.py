from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shotforge.config import Settings, get_settings
from shotforge.observation.observers import FrameObserver, HeuristicFrameObserver, VLMFrameObserver
from shotforge.observation.providers.vlm import (
    describe_frame_with_ollama,
    describe_frame_with_openai_compatible,
)


@dataclass(frozen=True)
class ObserverProviderDescriptor:
    provider_id: str
    display_name: str
    provider_type: str
    available: bool
    requires_model: bool
    requires_base_url: bool
    requires_api_key: bool
    default_base_url: str = ""
    default_model_hint: str = ""
    description: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "provider_type": self.provider_type,
            "available": self.available,
            "requires_model": self.requires_model,
            "requires_base_url": self.requires_base_url,
            "requires_api_key": self.requires_api_key,
            "default_base_url": self.default_base_url,
            "default_model_hint": self.default_model_hint,
            "description": self.description,
        }


def build_observer_provider_catalog(settings: Settings | None = None) -> list[ObserverProviderDescriptor]:
    settings = settings or get_settings()
    return [
        ObserverProviderDescriptor(
            provider_id="prompt-proxy",
            display_name="Prompt proxy observer",
            provider_type="test",
            available=True,
            requires_model=False,
            requires_base_url=False,
            requires_api_key=False,
            description="Uses prompt and storyboard text when no visual model is configured.",
        ),
        ObserverProviderDescriptor(
            provider_id="openai-vision",
            display_name="OpenAI-compatible vision",
            provider_type="cloud_or_gateway",
            available=bool(settings.vlm_model and settings.vlm_api_key),
            requires_model=True,
            requires_base_url=False,
            requires_api_key=True,
            default_model_hint="gpt-4o-mini",
            description="Calls an OpenAI-compatible chat-completions vision endpoint.",
        ),
        ObserverProviderDescriptor(
            provider_id="ollama-vision",
            display_name="Ollama vision",
            provider_type="local",
            available=bool(settings.vlm_model and settings.vlm_base_url),
            requires_model=True,
            requires_base_url=True,
            requires_api_key=False,
            default_base_url="http://localhost:11434",
            default_model_hint="qwen2.5vl:7b",
            description="Calls Ollama's native vision chat endpoint with extracted frames.",
        ),
        ObserverProviderDescriptor(
            provider_id="vllm-vlm",
            display_name="vLLM VLM",
            provider_type="local",
            available=bool(settings.vlm_model and settings.vlm_base_url),
            requires_model=True,
            requires_base_url=True,
            requires_api_key=False,
            default_base_url="http://localhost:8000/v1",
            default_model_hint="Qwen/Qwen2.5-VL-7B-Instruct",
            description="Calls a local OpenAI-compatible vLLM vision endpoint.",
        ),
    ]


def build_configured_frame_observer(settings: Settings | None = None) -> FrameObserver:
    settings = settings or get_settings()
    provider_id = settings.observer_provider
    if provider_id == "prompt-proxy":
        return HeuristicFrameObserver()
    if provider_id == "ollama-vision":
        return VLMFrameObserver(
            lambda frame_path, context: describe_frame_with_ollama(
                frame_path,
                context,
                model=settings.vlm_model,
                base_url=settings.vlm_base_url or "http://localhost:11434",
                timeout_seconds=settings.vlm_timeout_seconds,
            ),
            provider_id=provider_id,
        )
    if provider_id == "vllm-vlm":
        return VLMFrameObserver(
            lambda frame_path, context: describe_frame_with_openai_compatible(
                frame_path,
                context,
                model=settings.vlm_model,
                base_url=settings.vlm_base_url,
                api_key=settings.vlm_api_key or "local",
                require_json=settings.vlm_require_json,
                timeout_seconds=settings.vlm_timeout_seconds,
            ),
            provider_id=provider_id,
        )
    if provider_id == "openai-vision":
        return VLMFrameObserver(
            lambda frame_path, context: describe_frame_with_openai_compatible(
                frame_path,
                context,
                model=settings.vlm_model,
                base_url=settings.vlm_base_url,
                api_key=settings.vlm_api_key,
                require_json=settings.vlm_require_json,
                timeout_seconds=settings.vlm_timeout_seconds,
            ),
            provider_id=provider_id,
        )
    return HeuristicFrameObserver()
