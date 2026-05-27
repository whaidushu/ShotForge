from __future__ import annotations

from typing import Literal
from typing import Protocol

from pydantic import BaseModel, Field

from shotforge.core.project_state import GeneratedResult
from shotforge.core.project_state import ProjectState


CostMode = Literal["free", "local", "paid", "unknown"]


class GeneratorCapabilities(BaseModel):
    supports_video: bool = True
    supports_image_to_video: bool = False
    supports_audio: bool = False
    supports_batch: bool = False
    supported_aspect_ratios: list[str] = Field(default_factory=lambda: ["16:9", "9:16", "1:1"])
    max_duration_seconds: int | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class GenerationCostEstimate(BaseModel):
    provider_id: str
    estimated_cost: float = 0.0
    currency: str = "USD"
    cost_mode: CostMode = "unknown"
    notes: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class GeneratorProvider(Protocol):
    provider_id: str
    display_name: str

    def generate(self, state: ProjectState) -> GeneratedResult:
        """Generate artifacts from a project state."""

    def supports_real_generation(self) -> bool:
        """Return True when the provider calls a real external or local generator."""

    def estimate_cost(self, state: ProjectState) -> GenerationCostEstimate:
        """Estimate generation cost before the provider is invoked."""

    def capabilities(self) -> GeneratorCapabilities:
        """Describe provider limits and supported modalities."""
