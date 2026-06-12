from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ShotForge"
    storage_root: Path = Path("data")
    runs_dir: Path = Path("data/runs")
    versions_dir: Path = Path("data/versions")
    knowledge_base_path: Path = Path("data/knowledge_base.json")
    memory_store_path: Path = Path("data/memory.jsonl")
    provider_profiles_path: Path = Path("data/provider_profiles.json")
    default_duration_seconds: int = 24
    llm_provider: Literal["mock", "openai-compatible", "ollama", "vllm"] = "mock"
    llm_model: str = "mock"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 60.0
    evaluator_mode: Literal["mock", "llm", "hybrid"] = "mock"
    comfyui_enabled: bool = False
    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_workflows_dir: str = ""
    comfyui_workflow_id: str = "wan2_2_i2v_empty_start"
    comfyui_timeout_seconds: float = 900.0
    comfyui_width: int = 320
    comfyui_height: int = 320
    comfyui_length: int = 9
    comfyui_fps: float = 8.0
    comfyui_max_shots: int = 0
    comfyui_vae_dir: str = ""
    observer_provider: Literal["prompt-proxy", "openai-vision", "ollama-vision", "vllm-vlm"] = (
        "prompt-proxy"
    )
    vlm_model: str = ""
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    vlm_frame_sample_count: int = 4
    vlm_confidence_threshold: float = 0.65
    vlm_require_json: bool = True
    vlm_timeout_seconds: float = 90.0

    model_config = SettingsConfigDict(env_prefix="SHOTFORGE_", env_file=".env")

    def ensure_dirs(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.provider_profiles_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
