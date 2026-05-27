from __future__ import annotations

from shotforge.core.project_state import GeneratedResult, GeneratedShotResult, ProjectState
from shotforge.generators.base import GenerationCostEstimate, GeneratorCapabilities


class MockGenerator:
    provider_id = "mock"
    display_name = "Mock Generator"

    def supports_real_generation(self) -> bool:
        return False

    def capabilities(self) -> GeneratorCapabilities:
        return GeneratorCapabilities(
            supports_video=True,
            supports_image_to_video=False,
            supports_audio=False,
            supports_batch=True,
            max_duration_seconds=None,
            metadata={"purpose": "deterministic development and evaluation harness"},
        )

    def estimate_cost(self, state: ProjectState) -> GenerationCostEstimate:
        return GenerationCostEstimate(
            provider_id=self.provider_id,
            estimated_cost=0.0,
            cost_mode="free",
            notes="Deterministic mock generation has no external model cost.",
            metadata={"shot_count": len(state.shots)},
        )

    def generate(self, state: ProjectState) -> GeneratedResult:
        cost = self.estimate_cost(state)
        shots = []
        for shot in state.shots:
            prompt = next(item for item in state.prompt_package.prompts if item.shot_id == shot.shot_id)
            signals = self._quality_signals(state, shot.shot_id, shot.index)
            shots.append(
                GeneratedShotResult(
                    shot_id=shot.shot_id,
                    prompt_id=prompt.shot_id,
                    mock_video_uri=f"mock://{state.run_id}/{shot.shot_id}",
                    duration_seconds=shot.duration_seconds,
                    observed_summary=self._summary(state.language, shot.title, shot.shot_id),
                    detected_elements=[shot.title, shot.shot_type, state.style],
                    motion_summary=shot.motion.subject_motion if shot.motion else "",
                    audio_summary=next(
                        (item.music for item in state.audio_cues if item.shot_id == shot.shot_id),
                        "",
                    ),
                    quality_signals=signals,
                    metadata={
                        "generator_mode": "deterministic_mock",
                        "extension_note": "Replace this provider with real generators in V3.",
                    },
                )
            )

        result = GeneratedResult(
            project_id=state.project_id,
            run_id=state.run_id,
            version=state.version,
            provider="mock",
            status="mocked",
            shots=shots,
            artifact_refs=[shot.mock_video_uri for shot in shots],
            metadata={
                "source": "MockGenerator",
                "provider_id": self.provider_id,
                "display_name": self.display_name,
                "supports_real_generation": self.supports_real_generation(),
                "supports_evaluation": True,
                "cost_estimate": cost.model_dump(mode="json"),
                "capabilities": self.capabilities().model_dump(mode="json"),
            },
        )
        state.generation_results.append(result)
        state.touch()
        return result

    def _summary(self, language: str, title: str, shot_id: str) -> str:
        if language == "zh":
            return f"{shot_id} 模拟生成了“{title}”段落，但部分动作、情绪或声音点位可能偏弱。"
        return f"{shot_id} mocked a '{title}' beat with possible weak action, emotion, or audio timing."

    def _quality_signals(self, state: ProjectState, shot_id: str, shot_index: int) -> dict[str, float]:
        base = {
            "character_consistency": 0.82,
            "scene_consistency": 0.8,
            "action_clarity": 0.78,
            "emotional_intensity": 0.76,
            "camera_expression": 0.77,
            "pacing_progression": 0.74,
            "reversal_expression": 0.66,
            "audio_timing": 0.75,
            "prompt_executability": 0.84,
        }
        if shot_index == 2:
            base["action_clarity"] = 0.58
            base["pacing_progression"] = 0.63
        if shot_index == 3:
            base["emotional_intensity"] = 0.55
            base["reversal_expression"] = 0.48
        if shot_index == 4:
            base["audio_timing"] = 0.6
            base["camera_expression"] = 0.68
        correction_types = self._correction_types_for_shot(state, shot_id)
        if "action" in correction_types:
            base["action_clarity"] = min(0.92, base["action_clarity"] + 0.16)
            base["pacing_progression"] = min(0.9, base["pacing_progression"] + 0.08)
        if "emotion" in correction_types:
            base["emotional_intensity"] = min(0.9, base["emotional_intensity"] + 0.18)
            base["reversal_expression"] = min(0.86, base["reversal_expression"] + 0.1)
        if "prompt" in correction_types:
            base["prompt_executability"] = min(0.94, base["prompt_executability"] + 0.08)
        if "character" in correction_types:
            base["character_consistency"] = min(0.92, base["character_consistency"] + 0.08)
        if "scene" in correction_types:
            base["scene_consistency"] = min(0.92, base["scene_consistency"] + 0.1)
        if "camera" in correction_types:
            base["camera_expression"] = min(0.9, base["camera_expression"] + 0.12)
        if "audio" in correction_types:
            base["audio_timing"] = min(0.9, base["audio_timing"] + 0.15)
        return base

    def _correction_types_for_shot(self, state: ProjectState, shot_id: str) -> set[str]:
        correction_types = set()
        for patch in state.correction_patches:
            if any(operation.target_id == shot_id for operation in patch.operations):
                correction_type = patch.metadata.get("correction_type")
                if correction_type:
                    correction_types.add(str(correction_type))
        return correction_types
