from __future__ import annotations

import json
from pathlib import Path
import re
from zlib import crc32

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
        workflow_id: str | None = None,
    ):
        settings = get_settings()
        self.client = client or ComfyUIClient(base_url=settings.comfyui_base_url)
        self.workflow_registry = workflow_registry or build_workflow_registry()
        self.workflow_id = workflow_id or settings.comfyui_workflow_id
        self.resolver = ComfyUIArtifactResolver()

    def supports_real_generation(self) -> bool:
        return True

    def capabilities(self) -> GeneratorCapabilities:
        is_video = self._workflow_supports_video()
        return GeneratorCapabilities(
            supports_video=is_video,
            supports_image_to_video=False,
            supports_audio=False,
            supports_batch=False,
            supported_aspect_ratios=["1:1"],
            max_duration_seconds=None,
            metadata={
                "runtime": "comfyui",
                "workflow_id": self.workflow_id,
                "status": "experimental",
                "base_url": self.client.base_url,
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
        version_dir = get_settings().runs_dir / state.run_id / "iterations" / self._version_label(state)
        prompt_dir = version_dir / "prompts"
        workflow_dir = version_dir / "workflows"
        video_dir = version_dir / "videos"
        for directory in [prompt_dir, workflow_dir, video_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        max_shots = get_settings().comfyui_max_shots
        shots = state.shots[:max_shots] if max_shots > 0 else state.shots
        generated_shots = [
            self._generate_shot(state, shot.shot_id, prompt_dir, workflow_dir, video_dir)
            for shot in shots
        ]
        skipped_shot_ids = [shot.shot_id for shot in state.shots[len(shots) :]]
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
                "iteration_dir": str(version_dir),
                "prompt_dir": str(prompt_dir),
                "workflow_dir": str(workflow_dir),
                "video_dir": str(video_dir),
                "generated_shot_count": len(generated_shots),
                "skipped_shot_ids": skipped_shot_ids,
                "cost_estimate": self.estimate_cost(state).model_dump(mode="json"),
                "capabilities": self.capabilities().model_dump(mode="json"),
            },
        )
        state.generation_results.append(result)
        state.touch()
        return result

    def _generate_shot(
        self,
        state: ProjectState,
        shot_id: str,
        prompt_dir: Path,
        workflow_dir: Path,
        video_dir: Path,
    ) -> GeneratedShotResult:
        shot = next(item for item in state.shots if item.shot_id == shot_id)
        prompt = next(item for item in state.prompt_package.prompts if item.shot_id == shot_id)
        template = self.workflow_registry.get(self.workflow_id)
        settings = get_settings()
        version_label = self._version_label(state)
        shot_slug = self._shot_slug(shot_id, shot.title)
        base_name = f"{version_label}_{shot_slug}"
        comfy_prefix = f"shotforge/{state.run_id}/{version_label}/{base_name}"
        workflow = template.bind(
            {
                "prompt": self._provider_prompt(prompt),
                "negative_prompt": prompt.negative_prompt,
                "shot_id": shot_id,
                "width": settings.comfyui_width,
                "height": settings.comfyui_height,
                "length": settings.comfyui_length,
                "fps": settings.comfyui_fps,
                "seed": self._seed_for_shot(state.run_id, shot_id),
                "filename_prefix": comfy_prefix,
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "vae_name": "wan_2.1_vae.safetensors",
                "high_noise_unet": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                "low_noise_unet": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
                "high_noise_lora": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
                "low_noise_lora": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
            }
        )
        prompt_text_path = prompt_dir / f"{base_name}.txt"
        prompt_json_path = prompt_dir / f"{base_name}.json"
        workflow_path = workflow_dir / f"{base_name}.api.json"
        provider_prompt = self._provider_prompt(prompt)
        prompt_text_path.write_text(provider_prompt, encoding="utf-8")
        prompt_json_path.write_text(
            json.dumps(prompt.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        workflow_path.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
        prompt_id = self.client.queue_prompt(workflow)
        outputs = self.client.wait_for_outputs(prompt_id, timeout_seconds=settings.comfyui_timeout_seconds)
        artifacts = self.resolver.from_outputs(outputs)
        output_path = self.resolver.download_first(self.client, artifacts, video_dir, base_name)
        artifact_uri = str(output_path) if output_path else f"comfyui://{prompt_id}/{shot_id}"
        return GeneratedShotResult(
            shot_id=shot_id,
            prompt_id=prompt_id,
            mock_video_uri=artifact_uri,
            duration_seconds=prompt.parameters.get("duration_seconds", settings.comfyui_length),
            observed_summary=f"ComfyUI generated {shot_id} with workflow {self.workflow_id}.",
            detected_elements=[],
            motion_summary=f"Local ComfyUI video generation at {settings.comfyui_width}x{settings.comfyui_height}, {settings.comfyui_length} frames, {settings.comfyui_fps} fps.",
            audio_summary="",
            quality_signals=self._quality_signals_from_prompt(provider_prompt),
            metadata={
                "artifact_path": str(output_path) if output_path else "",
                "artifact_uri": artifact_uri,
                "artifact_count": len(artifacts),
                "workflow_id": self.workflow_id,
                "comfyui_base_url": self.client.base_url,
                "iteration": version_label,
                "prompt_text_path": str(prompt_text_path),
                "prompt_json_path": str(prompt_json_path),
                "workflow_api_path": str(workflow_path),
                "video_dir": str(video_dir),
                "local_filename": output_path.name if output_path else "",
                "comfyui_filename_prefix": comfy_prefix,
            },
        )

    def _seed_for_shot(self, run_id: str, shot_id: str) -> int:
        return crc32(f"{run_id}:{shot_id}".encode("utf-8")) & 0xFFFFFFFF

    def _provider_prompt(self, prompt) -> str:
        parts = [prompt.prompt]
        if prompt.structured_template is not None:
            parts.append(prompt.structured_template.render())
        return "\n".join(part.strip() for part in parts if part and part.strip())

    def _version_label(self, state: ProjectState) -> str:
        return f"v{state.version:03d}"

    def _shot_slug(self, shot_id: str, title: str) -> str:
        raw = f"{shot_id}_{title}".lower()
        slug = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
        return slug or shot_id

    def _workflow_supports_video(self) -> bool:
        try:
            workflow = self.workflow_registry.get(self.workflow_id).workflow
        except Exception:
            return self.workflow_id.startswith("wan2_2")
        video_nodes = {"CreateVideo", "SaveVideo", "SaveWEBM", "SaveAnimatedWEBP"}
        return any(
            isinstance(node, dict) and str(node.get("class_type", "")) in video_nodes
            for node in workflow.values()
        )

    def _quality_signals_from_prompt(self, prompt: str) -> dict[str, float]:
        text = prompt.lower()

        def score(*groups: tuple[str, ...]) -> float:
            value = 0.5
            for keywords in groups:
                if any(keyword in text for keyword in keywords):
                    value += 0.04
            return min(value, 0.86)

        return {
            "character_consistency": score(
                ("primary subject", "character"),
                ("silhouette",),
                ("preserve", "same"),
                ("identity", "wardrobe"),
                ("continuity",),
            ),
            "scene_consistency": score(
                ("environment",),
                ("layered", "spatial"),
                ("location",),
                ("anchor",),
                ("stable",),
            ),
            "action_clarity": score(
                ("moves", "action"),
                ("clear intent", "readable"),
                ("repairs", "repair"),
                ("broken", "vague"),
                ("launch", "outcome"),
            ),
            "emotional_intensity": score(
                ("rushed", "pressure", "tense"),
                ("broken", "vague"),
                ("clear",),
                ("confidence", "focused"),
                ("cinematic",),
            ),
            "camera_expression": score(
                ("wide",),
                ("push-in",),
                ("tracking", "close-up", "orbit"),
                ("camera",),
                ("establishing",),
            ),
            "pacing_progression": score(
                ("hook", "beat"),
                ("starts",),
                ("then",),
                ("transition", "pacing"),
                ("launch", "resolution"),
            ),
            "reversal_expression": score(
                ("vague", "broken"),
                ("then",),
                ("repairs", "repair"),
                ("clear",),
                ("launch",),
            ),
            "audio_timing": score(
                ("audio",),
                ("pulse",),
                ("texture",),
                ("timing",),
                ("beat",),
            ),
            "prompt_executability": score(
                ("subject", "primary subject"),
                ("environment", "location"),
                ("camera", "wide", "close-up", "tracking"),
                ("clear", "readable", "specific"),
            ),
        }
