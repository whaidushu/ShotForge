from __future__ import annotations

from typing import Any

from shotforge.app.services.provider_preflight import ProviderPreflightService
from shotforge.app.services.provider_profiles import (
    ProviderProfile,
    ProviderProfileStore,
    profile_id_from_name,
)
from shotforge.app.services.provider_runtime import ProviderRuntimeService
from shotforge.app.services.provider_workflows import ComfyUIWorkflowService
from shotforge.app.services.smoke_test_service import SmokeTestService
from shotforge.comfyui import default_user_workflows_dir
from shotforge.config import get_settings
from shotforge.core.project_state import ProjectState
from shotforge.generators import build_generator_catalog
from shotforge.llm.registry import build_llm_catalog
from shotforge.observation.providers import build_observer_provider_catalog


class ProviderService:
    def __init__(
        self,
        *,
        runtime_service: ProviderRuntimeService | None = None,
        workflow_service: ComfyUIWorkflowService | None = None,
        preflight_service: ProviderPreflightService | None = None,
        smoke_test_service: SmokeTestService | None = None,
    ) -> None:
        self.runtime_service = runtime_service or ProviderRuntimeService()
        self.workflow_service = workflow_service or ComfyUIWorkflowService()
        self.preflight_service = preflight_service or ProviderPreflightService(self.workflow_service)
        self.smoke_test_service = smoke_test_service or SmokeTestService(self.runtime_service)

    def available_generator_providers(self, *, include_test: bool = False) -> list[dict[str, Any]]:
        registry = build_generator_catalog()
        providers = []
        for provider_id in registry.list(available_only=False):
            if provider_id == "mock" and not include_test:
                continue
            provider = registry.get(provider_id, require_available=False)
            providers.append(
                {
                    "provider_id": provider.provider_id,
                    "display_name": provider.display_name,
                    "supports_real_generation": provider.supports_real_generation(),
                    "available": registry.is_available(provider_id),
                }
            )
        return providers

    def available_llm_providers(self, *, include_test: bool = False) -> list[dict[str, Any]]:
        registry = build_llm_catalog()
        providers = []
        for provider_id in registry.list(available_only=False):
            if provider_id == "mock" and not include_test:
                continue
            provider = registry.get(provider_id, require_available=False)
            providers.append(
                {
                    "provider_id": provider.model_name,
                    "display_name": provider.display_name,
                    "available": registry.is_available(provider_id),
                    "cost_mode": provider.cost_mode.value,
                    "model": getattr(provider, "model", provider.model_name),
                    "base_url": getattr(provider, "base_url", ""),
                }
            )
        return providers

    def available_observer_providers(self, *, include_test: bool = False) -> list[dict[str, Any]]:
        providers = []
        for provider in build_observer_provider_catalog():
            if provider.provider_id == "prompt-proxy" and not include_test:
                continue
            providers.append(provider.public_dict())
        return providers

    def available_comfyui_workflows(self, root: str | None = None) -> list[dict[str, Any]]:
        return self.workflow_service.available_workflows(root=root)

    def comfyui_workflow_status(self, root: str | None = None) -> dict[str, Any]:
        if root is None:
            root = self.default_provider_profile().comfyui_workflows_dir
        return self.workflow_service.workflow_status(root=root)

    def provider_profiles(self, *, include_test: bool = True) -> list[dict[str, Any]]:
        profiles = ProviderProfileStore().list()
        if not include_test:
            profiles = [
                profile
                for profile in profiles
                if profile.generator_provider_id != "mock" and profile.llm_provider_id != "mock"
            ]
        return [profile.public_dict() for profile in profiles]

    def default_provider_profile(self) -> ProviderProfile:
        store = ProviderProfileStore()
        profiles = [
            profile
            for profile in store.list()
            if profile.generator_provider_id != "mock" and profile.llm_provider_id != "mock"
        ]
        if profiles:
            return profiles[0]
        settings = get_settings()
        llm_provider_id = settings.llm_provider if settings.llm_provider != "mock" else "ollama"
        llm_model = settings.llm_model if settings.llm_provider != "mock" else "qwen2.5:7b"
        evaluator_mode = settings.evaluator_mode if settings.evaluator_mode != "mock" else "llm"
        return ProviderProfile(
            profile_id="local-real",
            name="Local real generation",
            llm_provider_id=llm_provider_id,
            llm_model=llm_model,
            llm_base_url=settings.llm_base_url,
            llm_api_key=settings.llm_api_key,
            evaluator_mode=evaluator_mode,
            generator_provider_id="comfyui",
            comfyui_base_url=settings.comfyui_base_url,
            comfyui_workflows_dir=settings.comfyui_workflows_dir or str(default_user_workflows_dir()),
            comfyui_workflow_id=settings.comfyui_workflow_id,
            comfyui_width=settings.comfyui_width,
            comfyui_height=settings.comfyui_height,
            comfyui_length=settings.comfyui_length,
            comfyui_fps=settings.comfyui_fps,
            comfyui_max_shots=settings.comfyui_max_shots,
            observer_provider_id=settings.observer_provider,
            vlm_model=settings.vlm_model,
            vlm_base_url=settings.vlm_base_url,
            vlm_api_key=settings.vlm_api_key,
            vlm_frame_sample_count=settings.vlm_frame_sample_count,
            vlm_confidence_threshold=settings.vlm_confidence_threshold,
            vlm_require_json=settings.vlm_require_json,
        )

    def profile_from_payload(self, payload: Any) -> ProviderProfile:
        default_profile = self.default_provider_profile()
        return ProviderProfile(
            profile_id=profile_id_from_name(payload.provider_profile_id or payload.provider_profile_name),
            name=payload.provider_profile_name or payload.provider_profile_id or default_profile.name,
            llm_provider_id=payload.llm_provider_id or default_profile.llm_provider_id,
            llm_model=payload.llm_model or default_profile.llm_model,
            llm_base_url=payload.llm_base_url or "",
            llm_api_key=payload.llm_api_key or "",
            evaluator_mode=payload.evaluator_mode or default_profile.evaluator_mode,
            generator_provider_id=payload.generator_provider_id or default_profile.generator_provider_id,
            comfyui_base_url=payload.comfyui_base_url or default_profile.comfyui_base_url,
            comfyui_workflows_dir=payload.comfyui_workflows_dir or default_profile.comfyui_workflows_dir,
            comfyui_workflow_id=payload.comfyui_workflow_id or default_profile.comfyui_workflow_id,
            comfyui_width=payload.comfyui_width or default_profile.comfyui_width,
            comfyui_height=payload.comfyui_height or default_profile.comfyui_height,
            comfyui_length=payload.comfyui_length or default_profile.comfyui_length,
            comfyui_fps=payload.comfyui_fps or default_profile.comfyui_fps,
            comfyui_max_shots=payload.comfyui_max_shots or default_profile.comfyui_max_shots,
            observer_provider_id=payload.observer_provider_id or default_profile.observer_provider_id,
            vlm_model=payload.vlm_model or default_profile.vlm_model,
            vlm_base_url=payload.vlm_base_url or default_profile.vlm_base_url,
            vlm_api_key=payload.vlm_api_key or "",
            vlm_frame_sample_count=payload.vlm_frame_sample_count
            or default_profile.vlm_frame_sample_count,
            vlm_confidence_threshold=payload.vlm_confidence_threshold
            or default_profile.vlm_confidence_threshold,
            vlm_require_json=default_profile.vlm_require_json
            if payload.vlm_require_json is None
            else payload.vlm_require_json,
        )

    def profile_from_form(
        self,
        *,
        provider_profile_id: str,
        provider_profile_name: str,
        llm_provider_id: str,
        llm_model: str,
        llm_base_url: str,
        llm_api_key: str,
        evaluator_mode: str,
        generator_provider_id: str,
        comfyui_base_url: str,
        comfyui_workflows_dir: str,
        comfyui_workflow_id: str,
        comfyui_width: int,
        comfyui_height: int,
        comfyui_length: int,
        comfyui_fps: float,
        comfyui_max_shots: int,
        observer_provider_id: str,
        vlm_model: str,
        vlm_base_url: str,
        vlm_api_key: str,
        vlm_frame_sample_count: int,
        vlm_confidence_threshold: float,
        vlm_require_json: bool,
    ) -> ProviderProfile:
        default_profile = self.default_provider_profile()
        return ProviderProfile(
            profile_id=profile_id_from_name(provider_profile_id or provider_profile_name),
            name=provider_profile_name or provider_profile_id or default_profile.name,
            llm_provider_id=llm_provider_id,
            llm_model=llm_model,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            evaluator_mode=evaluator_mode,
            generator_provider_id=generator_provider_id,
            comfyui_base_url=comfyui_base_url or default_profile.comfyui_base_url,
            comfyui_workflows_dir=comfyui_workflows_dir or default_profile.comfyui_workflows_dir,
            comfyui_workflow_id=comfyui_workflow_id or default_profile.comfyui_workflow_id,
            comfyui_width=comfyui_width,
            comfyui_height=comfyui_height,
            comfyui_length=comfyui_length,
            comfyui_fps=comfyui_fps,
            comfyui_max_shots=comfyui_max_shots,
            observer_provider_id=observer_provider_id,
            vlm_model=vlm_model,
            vlm_base_url=vlm_base_url,
            vlm_api_key=vlm_api_key,
            vlm_frame_sample_count=vlm_frame_sample_count,
            vlm_confidence_threshold=vlm_confidence_threshold,
            vlm_require_json=vlm_require_json,
        )

    def validate_generator_provider_id(self, provider_id: str) -> str:
        try:
            provider = build_generator_catalog().get(provider_id, require_available=False)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        if provider_id != "mock" and not provider.supports_real_generation():
            raise ValueError(f"Provider is not a real generator: {provider_id}")
        if provider_id not in {"mock", "comfyui"} and not build_generator_catalog().is_available(provider_id):
            raise ValueError(f"Provider is not enabled for local generation: {provider_id}")
        return provider_id

    def apply_provider_profile(self, profile: ProviderProfile) -> None:
        self.runtime_service.apply_provider_profile(profile)

    def scoped_provider_profile(self, profile: ProviderProfile):
        return self.runtime_service.scoped_provider_profile(profile)

    def record_provider_profile_metadata(self, state: ProjectState, profile: ProviderProfile) -> None:
        self.runtime_service.record_provider_profile_metadata(state, profile)

    def record_provider_config_metadata(self, state: ProjectState) -> None:
        self.runtime_service.record_provider_config_metadata(state)

    def preflight_provider_profile(self, profile: ProviderProfile) -> dict[str, Any]:
        return self.preflight_service.preflight_provider_profile(profile)

    def run_internal_test_chain(self) -> dict[str, Any]:
        return self.smoke_test_service.run_internal_test_chain()
