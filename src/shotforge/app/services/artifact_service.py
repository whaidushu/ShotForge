from __future__ import annotations

from pathlib import Path
from typing import Any

from shotforge.core.project_state import ProjectState


class ArtifactNotFoundError(FileNotFoundError):
    pass


class ArtifactService:
    def generation_artifacts(self, state: ProjectState | None) -> list[dict[str, Any]]:
        if state is None:
            return []
        artifacts: list[dict[str, Any]] = []
        for generation in state.generation_results:
            for shot in generation.shots:
                metadata = shot.metadata
                version = str(metadata.get("iteration") or f"v{generation.version:03d}")
                artifacts.append(
                    {
                        "provider": generation.provider,
                        "version": generation.version,
                        "iteration": version,
                        "shot_id": shot.shot_id,
                        "status": generation.status,
                        "video_filename": metadata.get("local_filename") or Path(shot.mock_video_uri).name,
                        "video_path": shot.mock_video_uri,
                        "prompt_text_path": metadata.get("prompt_text_path", ""),
                        "prompt_json_path": metadata.get("prompt_json_path", ""),
                        "workflow_api_path": metadata.get("workflow_api_path", ""),
                        "video_url": f"/api/runs/{state.run_id}/artifacts/video/{version}/{shot.shot_id}",
                        "prompt_url": f"/api/runs/{state.run_id}/artifacts/prompt/{version}/{shot.shot_id}",
                        "prompt_json_url": f"/api/runs/{state.run_id}/artifacts/prompt_json/{version}/{shot.shot_id}",
                        "workflow_url": f"/api/runs/{state.run_id}/artifacts/workflow/{version}/{shot.shot_id}",
                    }
                )
        return artifacts

    def artifact_path_from_state(
        self,
        state: ProjectState,
        artifact_kind: str,
        iteration: str,
        shot_id: str,
    ) -> Path:
        metadata_key = {
            "video": "artifact_path",
            "prompt": "prompt_text_path",
            "prompt_json": "prompt_json_path",
            "workflow": "workflow_api_path",
        }.get(artifact_kind)
        if metadata_key is None:
            raise ValueError("artifact_kind must be video, prompt, prompt_json, or workflow")
        for generation in state.generation_results:
            for shot in generation.shots:
                shot_iteration = str(shot.metadata.get("iteration") or f"v{generation.version:03d}")
                if shot.shot_id == shot_id and shot_iteration == iteration:
                    raw_path = shot.metadata.get(metadata_key)
                    if raw_path:
                        path = Path(raw_path)
                        if not path.is_absolute():
                            path = Path.cwd() / path
                        if path.exists():
                            return path
        raise ArtifactNotFoundError(f"Artifact not found: {artifact_kind}/{iteration}/{shot_id}")
