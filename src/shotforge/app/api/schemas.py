from __future__ import annotations

from pydantic import BaseModel, Field

from shotforge.core.project_state import OutputLanguage, ProjectState


class RunRequest(BaseModel):
    idea: str = Field(min_length=2)
    style: str = "cinematic"
    language: OutputLanguage = "zh"
    duration_seconds: int = Field(default=24, ge=6, le=180)
    with_evaluation: bool = False
    with_planning: bool = False
    rubric_id: str = "baseline_v1"
    max_iterations: int = Field(default=3, ge=2, le=10)
    provider_profile_id: str = "local-real"
    provider_profile_name: str = "Local real generation"
    generator_provider_id: str = "comfyui"
    llm_provider_id: str | None = "ollama"
    llm_model: str | None = "qwen2.5:7b"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    evaluator_mode: str | None = "llm"
    comfyui_base_url: str | None = None
    comfyui_workflows_dir: str | None = None
    comfyui_workflow_id: str | None = None
    comfyui_width: int | None = Field(default=None, ge=64, le=2048)
    comfyui_height: int | None = Field(default=None, ge=64, le=2048)
    comfyui_length: int | None = Field(default=None, ge=1, le=512)
    comfyui_fps: float | None = Field(default=None, ge=1, le=60)
    comfyui_max_shots: int | None = Field(default=None, ge=0, le=32)
    observer_provider_id: str | None = "prompt-proxy"
    vlm_model: str | None = ""
    vlm_base_url: str | None = ""
    vlm_api_key: str | None = ""
    vlm_frame_sample_count: int | None = Field(default=4, ge=1, le=16)
    vlm_confidence_threshold: float | None = Field(default=0.65, ge=0, le=1)
    vlm_require_json: bool = True


class RunResponse(BaseModel):
    project_id: str
    run_id: str
    version: int
    exports: dict[str, str]
    state: ProjectState


class PreflightRequest(BaseModel):
    provider_profile_id: str = "local-real"
    provider_profile_name: str = "Local real generation"
    generator_provider_id: str = "comfyui"
    llm_provider_id: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = ""
    llm_api_key: str = ""
    evaluator_mode: str = "llm"
    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_workflows_dir: str = ""
    comfyui_workflow_id: str = "wan2_2_i2v_empty_start"
    comfyui_width: int = Field(default=320, ge=64, le=2048)
    comfyui_height: int = Field(default=320, ge=64, le=2048)
    comfyui_length: int = Field(default=9, ge=1, le=512)
    comfyui_fps: float = Field(default=8.0, ge=1, le=60)
    comfyui_max_shots: int = Field(default=0, ge=0, le=32)
    observer_provider_id: str = "prompt-proxy"
    vlm_model: str = ""
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    vlm_frame_sample_count: int = Field(default=4, ge=1, le=16)
    vlm_confidence_threshold: float = Field(default=0.65, ge=0, le=1)
    vlm_require_json: bool = True
