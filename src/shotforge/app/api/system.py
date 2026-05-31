from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from shotforge.config import get_settings
from shotforge.core.capability_catalog import build_capability_catalog


def build_system_router() -> APIRouter:
    router = APIRouter(prefix="/api", tags=["system"])

    @router.get("/capabilities")
    def get_capabilities() -> dict[str, Any]:
        return build_capability_catalog()

    @router.get("/health")
    def get_health() -> dict[str, Any]:
        settings = get_settings()
        return {
            "status": "ok",
            "app_name": settings.app_name,
            "storage": {
                "storage_root": str(settings.storage_root),
                "runs_dir": str(settings.runs_dir),
                "versions_dir": str(settings.versions_dir),
                "knowledge_base_path": str(settings.knowledge_base_path),
                "memory_store_path": str(settings.memory_store_path),
                "runs_dir_exists": settings.runs_dir.exists(),
                "versions_dir_exists": settings.versions_dir.exists(),
            },
            "comfyui": {
                "enabled": settings.comfyui_enabled,
                "base_url": settings.comfyui_base_url,
                "workflow_id": settings.comfyui_workflow_id,
                "width": settings.comfyui_width,
                "height": settings.comfyui_height,
                "length": settings.comfyui_length,
                "fps": settings.comfyui_fps,
                "max_shots": settings.comfyui_max_shots,
            },
            "observer": {
                "provider": settings.observer_provider,
                "vlm_model": settings.vlm_model,
                "vlm_base_url": settings.vlm_base_url,
                "frame_sample_count": settings.vlm_frame_sample_count,
                "confidence_threshold": settings.vlm_confidence_threshold,
                "require_json": settings.vlm_require_json,
            },
        }

    return router
