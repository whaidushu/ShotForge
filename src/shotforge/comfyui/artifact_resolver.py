from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shotforge.comfyui.client import ComfyUIClient


@dataclass(frozen=True)
class ComfyUIArtifact:
    node_id: str
    filename: str
    subfolder: str = ""
    file_type: str = "output"


class ComfyUIArtifactResolver:
    def from_outputs(self, outputs: dict[str, Any]) -> list[ComfyUIArtifact]:
        artifacts: list[ComfyUIArtifact] = []
        for node_id, node_output in outputs.items():
            if not isinstance(node_output, dict):
                continue
            for key in ["images", "gifs", "videos"]:
                for item in node_output.get(key, []):
                    if isinstance(item, dict) and item.get("filename"):
                        artifacts.append(
                            ComfyUIArtifact(
                                node_id=str(node_id),
                                filename=str(item["filename"]),
                                subfolder=str(item.get("subfolder", "")),
                                file_type=str(item.get("type", "output")),
                            )
                        )
        return artifacts

    def download_first(
        self,
        client: ComfyUIClient,
        artifacts: list[ComfyUIArtifact],
        output_dir: Path,
        filename_prefix: str,
    ) -> Path | None:
        if not artifacts:
            return None
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact = artifacts[0]
        data = client.download_file(
            artifact.filename,
            subfolder=artifact.subfolder,
            file_type=artifact.file_type,
        )
        suffix = Path(artifact.filename).suffix or ".bin"
        output_path = output_dir / f"{filename_prefix}{suffix}"
        output_path.write_bytes(data)
        return output_path
