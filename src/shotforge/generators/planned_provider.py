from __future__ import annotations

from shotforge.core.project_state import GeneratedResult, ProjectState
from shotforge.generators.base import GenerationCostEstimate, GeneratorCapabilities


class PlannedGeneratorProvider:
    def __init__(
        self,
        provider_id: str,
        display_name: str,
        cost_mode: str = "unknown",
        supports_image_to_video: bool = True,
        supports_audio: bool = False,
    ):
        self.provider_id = provider_id
        self.display_name = display_name
        self._cost_mode = cost_mode
        self._supports_image_to_video = supports_image_to_video
        self._supports_audio = supports_audio

    def supports_real_generation(self) -> bool:
        return True

    def capabilities(self) -> GeneratorCapabilities:
        return GeneratorCapabilities(
            supports_video=True,
            supports_image_to_video=self._supports_image_to_video,
            supports_audio=self._supports_audio,
            supports_batch=False,
            max_duration_seconds=None,
            metadata={"status": "planned", "available": False},
        )

    def estimate_cost(self, state: ProjectState) -> GenerationCostEstimate:
        return GenerationCostEstimate(
            provider_id=self.provider_id,
            estimated_cost=0.0,
            cost_mode=self._cost_mode,
            notes="Provider is planned but not enabled in this POC build.",
            metadata={"shot_count": len(state.shots), "available": False},
        )

    def generate(self, state: ProjectState) -> GeneratedResult:
        raise NotImplementedError(f"{self.display_name} is planned but not enabled yet.")
