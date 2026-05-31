from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from shotforge.app.services.provider_profiles import ProviderProfile
from shotforge.config import get_settings
from shotforge.core.project_state import ProjectState


class ProviderRuntimeService:
    ENV_KEYS = [
        "SHOTFORGE_LLM_PROVIDER",
        "SHOTFORGE_LLM_MODEL",
        "SHOTFORGE_LLM_BASE_URL",
        "SHOTFORGE_LLM_API_KEY",
        "SHOTFORGE_EVALUATOR_MODE",
        "SHOTFORGE_COMFYUI_ENABLED",
        "SHOTFORGE_COMFYUI_BASE_URL",
        "SHOTFORGE_COMFYUI_WORKFLOWS_DIR",
        "SHOTFORGE_COMFYUI_WORKFLOW_ID",
        "SHOTFORGE_COMFYUI_WIDTH",
        "SHOTFORGE_COMFYUI_HEIGHT",
        "SHOTFORGE_COMFYUI_LENGTH",
        "SHOTFORGE_COMFYUI_FPS",
        "SHOTFORGE_COMFYUI_MAX_SHOTS",
        "SHOTFORGE_OBSERVER_PROVIDER",
        "SHOTFORGE_VLM_MODEL",
        "SHOTFORGE_VLM_BASE_URL",
        "SHOTFORGE_VLM_API_KEY",
        "SHOTFORGE_VLM_FRAME_SAMPLE_COUNT",
        "SHOTFORGE_VLM_CONFIDENCE_THRESHOLD",
        "SHOTFORGE_VLM_REQUIRE_JSON",
    ]

    def apply_provider_profile(self, profile: ProviderProfile) -> None:
        self.apply_provider_config(
            llm_provider_id=profile.llm_provider_id,
            llm_model=profile.llm_model,
            llm_base_url=profile.llm_base_url,
            llm_api_key=profile.llm_api_key,
            evaluator_mode=profile.evaluator_mode,
            generator_provider_id=profile.generator_provider_id,
            comfyui_base_url=profile.comfyui_base_url,
            comfyui_workflows_dir=profile.comfyui_workflows_dir,
            comfyui_workflow_id=profile.comfyui_workflow_id,
            comfyui_width=profile.comfyui_width,
            comfyui_height=profile.comfyui_height,
            comfyui_length=profile.comfyui_length,
            comfyui_fps=profile.comfyui_fps,
            comfyui_max_shots=profile.comfyui_max_shots,
            observer_provider_id=profile.observer_provider_id,
            vlm_model=profile.vlm_model,
            vlm_base_url=profile.vlm_base_url,
            vlm_api_key=profile.vlm_api_key,
            vlm_frame_sample_count=profile.vlm_frame_sample_count,
            vlm_confidence_threshold=profile.vlm_confidence_threshold,
            vlm_require_json=profile.vlm_require_json,
        )

    @contextmanager
    def scoped_provider_profile(self, profile: ProviderProfile) -> Iterator[None]:
        snapshot = {key: os.environ.get(key) for key in self.ENV_KEYS}
        try:
            self.apply_provider_profile(profile)
            yield
        finally:
            self.restore_env(snapshot)

    def restore_env(self, snapshot: dict[str, str | None]) -> None:
        for key, value in snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()

    def apply_provider_config(
        self,
        *,
        llm_provider_id: str | None = None,
        llm_model: str | None = None,
        llm_base_url: str | None = None,
        llm_api_key: str | None = None,
        evaluator_mode: str | None = None,
        generator_provider_id: str | None = None,
        comfyui_base_url: str | None = None,
        comfyui_workflows_dir: str | None = None,
        comfyui_workflow_id: str | None = None,
        comfyui_width: int | None = None,
        comfyui_height: int | None = None,
        comfyui_length: int | None = None,
        comfyui_fps: float | None = None,
        comfyui_max_shots: int | None = None,
        observer_provider_id: str | None = None,
        vlm_model: str | None = None,
        vlm_base_url: str | None = None,
        vlm_api_key: str | None = None,
        vlm_frame_sample_count: int | None = None,
        vlm_confidence_threshold: float | None = None,
        vlm_require_json: bool | None = None,
    ) -> None:
        updates: dict[str, Any] = {}
        if llm_provider_id:
            updates["LLM_PROVIDER"] = llm_provider_id
        if llm_model is not None:
            updates["LLM_MODEL"] = llm_model
        if llm_base_url is not None:
            updates["LLM_BASE_URL"] = llm_base_url
        if llm_api_key is not None:
            updates["LLM_API_KEY"] = llm_api_key
        if evaluator_mode:
            updates["EVALUATOR_MODE"] = evaluator_mode
        configure_comfyui = generator_provider_id == "comfyui"
        if configure_comfyui:
            updates["COMFYUI_ENABLED"] = "true"
        if configure_comfyui and comfyui_base_url is not None:
            updates["COMFYUI_BASE_URL"] = comfyui_base_url
        if configure_comfyui and comfyui_workflows_dir is not None:
            updates["COMFYUI_WORKFLOWS_DIR"] = comfyui_workflows_dir
        if configure_comfyui and comfyui_workflow_id is not None:
            updates["COMFYUI_WORKFLOW_ID"] = comfyui_workflow_id
        for key, value in {
            "COMFYUI_WIDTH": comfyui_width,
            "COMFYUI_HEIGHT": comfyui_height,
            "COMFYUI_LENGTH": comfyui_length,
            "COMFYUI_FPS": comfyui_fps,
            "COMFYUI_MAX_SHOTS": comfyui_max_shots,
        }.items():
            if configure_comfyui and value is not None:
                updates[key] = value
        if observer_provider_id:
            updates["OBSERVER_PROVIDER"] = observer_provider_id
        if vlm_model is not None:
            updates["VLM_MODEL"] = vlm_model
        if vlm_base_url is not None:
            updates["VLM_BASE_URL"] = vlm_base_url
        if vlm_api_key is not None:
            updates["VLM_API_KEY"] = vlm_api_key
        if vlm_frame_sample_count is not None:
            updates["VLM_FRAME_SAMPLE_COUNT"] = vlm_frame_sample_count
        if vlm_confidence_threshold is not None:
            updates["VLM_CONFIDENCE_THRESHOLD"] = vlm_confidence_threshold
        if vlm_require_json is not None:
            updates["VLM_REQUIRE_JSON"] = str(vlm_require_json).lower()
        for key, value in updates.items():
            os.environ[f"SHOTFORGE_{key}"] = str(value)
        if updates:
            get_settings.cache_clear()

    @staticmethod
    def record_provider_profile_metadata(state: ProjectState, profile: ProviderProfile) -> None:
        state.metadata["provider_profile_id"] = profile.profile_id
        state.metadata["provider_profile_name"] = profile.name

    @staticmethod
    def record_provider_config_metadata(state: ProjectState) -> None:
        settings = get_settings()
        state.metadata["llm_provider_id"] = settings.llm_provider
        state.metadata["llm_model"] = settings.llm_model
        state.metadata["llm_base_url"] = settings.llm_base_url
        state.metadata["evaluator_mode"] = settings.evaluator_mode
        state.metadata["comfyui_base_url"] = settings.comfyui_base_url
        state.metadata["comfyui_workflows_dir"] = settings.comfyui_workflows_dir
        state.metadata["comfyui_workflow_id"] = settings.comfyui_workflow_id
        state.metadata["comfyui_width"] = settings.comfyui_width
        state.metadata["comfyui_height"] = settings.comfyui_height
        state.metadata["comfyui_length"] = settings.comfyui_length
        state.metadata["comfyui_fps"] = settings.comfyui_fps
        state.metadata["comfyui_max_shots"] = settings.comfyui_max_shots
        state.metadata["observer_provider_id"] = settings.observer_provider
        state.metadata["vlm_model"] = settings.vlm_model
        state.metadata["vlm_base_url"] = settings.vlm_base_url
        state.metadata["vlm_frame_sample_count"] = settings.vlm_frame_sample_count
        state.metadata["vlm_confidence_threshold"] = settings.vlm_confidence_threshold
        state.metadata["vlm_require_json"] = settings.vlm_require_json
