from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from shotforge.core.project_state import PromptItem


class VideoGenerationResult(BaseModel):
    provider: str
    request_id: str
    status: str
    asset_uri: str | None = None


class VideoModelClient(Protocol):
    def submit(self, prompt: PromptItem) -> VideoGenerationResult:
        """Submit a scene prompt to an external video generation provider."""
