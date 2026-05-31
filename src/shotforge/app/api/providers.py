from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from shotforge.app.api.schemas import PreflightRequest
from shotforge.app.services.provider_profiles import ProviderProfile, ProviderProfileStore
from shotforge.app.services.provider_service import ProviderService
from shotforge.comfyui import default_user_workflows_dir
from shotforge.config import get_settings


def build_provider_router(provider_service: ProviderService) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["providers"])

    @router.get("/provider-profiles")
    def get_provider_profiles() -> dict[str, Any]:
        return {
            "profiles": provider_service.provider_profiles(),
            "default_profile": provider_service.default_provider_profile().public_dict(),
            "path": str(get_settings().provider_profiles_path),
        }

    @router.get("/observer-providers")
    def get_observer_providers() -> dict[str, Any]:
        return {
            "observer_providers": provider_service.available_observer_providers(include_test=True),
            "default_profile": provider_service.default_provider_profile().public_dict(),
        }

    @router.post("/provider-profiles")
    def save_provider_profile(profile: ProviderProfile) -> dict[str, Any]:
        saved = ProviderProfileStore().upsert(profile)
        return {"profile": saved.public_dict(), "path": str(get_settings().provider_profiles_path)}

    @router.post("/preflight")
    def run_preflight(payload: PreflightRequest) -> dict[str, Any]:
        profile = provider_service.profile_from_payload(payload)
        return provider_service.preflight_provider_profile(profile)

    @router.post("/test-chain")
    def run_test_chain() -> dict[str, Any]:
        return provider_service.run_internal_test_chain()

    @router.get("/comfyui/workflows")
    def get_comfyui_workflows(root: str | None = None) -> dict[str, Any]:
        settings = get_settings()
        default_profile = provider_service.default_provider_profile()
        workflow_status = provider_service.comfyui_workflow_status(root=root)
        return {
            "enabled": settings.comfyui_enabled or default_profile.generator_provider_id == "comfyui",
            "base_url": default_profile.comfyui_base_url or settings.comfyui_base_url,
            "workflow_id": default_profile.comfyui_workflow_id or settings.comfyui_workflow_id,
            "workflows_dir": root
            or default_profile.comfyui_workflows_dir
            or settings.comfyui_workflows_dir
            or str(default_user_workflows_dir()),
            "workflows": workflow_status["workflows"],
            "warnings": workflow_status["warnings"],
        }

    return router
