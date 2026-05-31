from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shotforge.config import get_settings


def profile_id_from_name(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")
    return normalized or "default"


class ProviderProfile(BaseModel):
    profile_id: str = "default"
    name: str = "Default local profile"
    llm_provider_id: str = "mock"
    llm_model: str = "mock"
    llm_base_url: str = ""
    llm_api_key: str = ""
    evaluator_mode: str = "mock"
    generator_provider_id: str = "mock"
    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_workflows_dir: str = ""
    comfyui_workflow_id: str = "wan2_2_i2v_empty_start"
    comfyui_width: int = 320
    comfyui_height: int = 320
    comfyui_length: int = 9
    comfyui_fps: float = 8.0
    comfyui_max_shots: int = 0
    observer_provider_id: str = "prompt-proxy"
    vlm_model: str = ""
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    vlm_frame_sample_count: int = 4
    vlm_confidence_threshold: float = 0.65
    vlm_require_json: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["has_llm_api_key"] = bool(self.llm_api_key)
        data["llm_api_key"] = ""
        data["has_vlm_api_key"] = bool(self.vlm_api_key)
        data["vlm_api_key"] = ""
        return data


class ProviderProfileStore:
    def __init__(self, path: Path | None = None):
        self.path = path or get_settings().provider_profiles_path

    def list(self) -> list[ProviderProfile]:
        payload = self._read()
        profiles = payload.get("profiles", [])
        return [ProviderProfile.model_validate(item) for item in profiles]

    def get(self, profile_id: str) -> ProviderProfile:
        for profile in self.list():
            if profile.profile_id == profile_id:
                return profile
        raise KeyError(f"Provider profile not found: {profile_id}")

    def default(self) -> ProviderProfile:
        profiles = self.list()
        if profiles:
            return profiles[0]
        return ProviderProfile()

    def upsert(self, profile: ProviderProfile) -> ProviderProfile:
        profile.profile_id = profile_id_from_name(profile.profile_id or profile.name)
        profile.name = profile.name.strip() or profile.profile_id
        profiles = [item for item in self.list() if item.profile_id != profile.profile_id]
        profiles.insert(0, profile)
        self._write({"profiles": [item.model_dump(mode="json") for item in profiles]})
        return profile

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"profiles": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"profiles": []}
        if not isinstance(data, dict):
            return {"profiles": []}
        data.setdefault("profiles", [])
        return data

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
