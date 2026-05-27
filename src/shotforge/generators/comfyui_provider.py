from __future__ import annotations

from pathlib import Path

from shotforge.comfyui import (
    ComfyUIArtifactResolver,
    ComfyUIClient,
    ComfyUIWorkflowRegistry,
    build_workflow_registry,
)
from shotforge.config import get_settings
from shotforge.core.project_state import GeneratedResult, GeneratedShotResult, ProjectState
from shotforge.generators.base import GenerationCostEstimate, GeneratorCapabilities


class ComfyUIProvider:
    provider_id = "comfyui"
    display_name = "ComfyUI Provider"

    def __init__(
        self,
        client: ComfyUIClient | None = None,
        workflow_registry: ComfyUIWorkflowRegistry | None = None,
        workflow_id: str = "txt2img_sd15",
    ):
        self.client = client or ComfyUIClient()
        self.workflow_registry = workflow_registry or build_workflow_registry()
        self.workflow_id = workflow_id
        self.resolver = ComfyUIArtifactResolver()

    def supports_real_generation(self) -> bool:
        return True

    def capabilities(self) -> GeneratorCapabilities:
        return GeneratorCapabilities(
            supports_video=False,
            supports_image_to_video=False,
            supports_audio=False,
            supports_batch=False,
            supported_aspect_ratios=["1:1"],
            metadata={
                "runtime": "comfyui",
                "workflow_id": self.workflow_id,
                "status": "experimental",
            },
        )

    def estimate_cost(self, state: ProjectState) -> GenerationCostEstimate:
        return GenerationCostEstimate(
            provider_id=self.provider_id,
            estimated_cost=0.0,
            cost_mode="local",
            notes="ComfyUI runs locally. Runtime availability depends on the local ComfyUI server.",
            metadata={"shot_count": len(state.shots), "workflow_id": self.workflow_id},
        )

    def generate(self, state: ProjectState) -> GeneratedResult:
        template = self.workflow_registry.get(self.workflow_id)
        output_dir = get_settings().runs_dir / state.run_id / "artifacts"
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_shots = [
            self._generate_shot(state, shot.shot_id, output_dir)
            for shot in state.shots
        ]
        result = GeneratedResult(
            project_id=state.project_id,
            run_id=state.run_id,
            version=state.version,
            provider=self.provider_id,
            status="completed",
            shots=generated_shots,
            artifact_refs=[shot.mock_video_uri for shot in generated_shots],
            metadata={
                "provider_id": self.provider_id,
                "display_name": self.display_name,
                "workflow_id": template.template_id,
                "supports_real_generation": True,
                "cost_estimate": self.estimate_cost(state).model_dump(mode="json"),
                "capabilities": self.capabilities().model_dump(mode="json"),
            },
        )
        state.generation_results.append(result)
        state.touch()
        return result

    def _generate_shot(self, state: ProjectState, shot_id: str, output_dir: Path) -> GeneratedShotResult:
        prompt = next(item for item in state.prompt_package.prompts if item.shot_id == shot_id)
        template = self.workflow_registry.get(self.workflow_id)
        workflow = template.bind(
            {
                "prompt": prompt.prompt,
                "negative_prompt": prompt.negative_prompt,
                "shot_id": shot_id,
            }
        )
        prompt_id = self.client.queue_prompt(workflow)
        outputs = self.client.wait_for_outputs(prompt_id)
        artifacts = self.resolver.from_outputs(outputs)
        output_path = self.resolver.download_first(self.client, artifacts, output_dir, shot_id)
        artifact_uri = str(output_path) if output_path else f"comfyui://{prompt_id}/{shot_id}"
        return GeneratedShotResult(
            shot_id=shot_id,
            prompt_id=prompt_id,
            mock_video_uri=artifact_uri,
            duration_seconds=4,
            observed_summary=f"ComfyUI generated {shot_id} with workflow {self.workflow_id}.",
            detected_elements=[],
            motion_summary="",
            audio_summary="",
            quality_signals=self._default_quality_signals(),
            metadata={
                "artifact_path": str(output_path) if output_path else "",
                "artifact_uri": artifact_uri,
                "artifact_count": len(artifacts),
                "workflow_id": self.workflow_id,
            },
        )

    def _default_quality_signals(self) -> dict[str, float]:
        return {
            "character_consistency": 0.5,
            "scene_consistency": 0.5,
            "action_clarity": 0.5,
            "emotional_intensity": 0.5,
            "camera_expression": 0.5,
            "pacing_progression": 0.5,
            "reversal_expression": 0.5,
            "audio_timing": 0.5,
            "prompt_executability": 0.5,
        }
