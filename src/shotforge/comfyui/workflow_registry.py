from __future__ import annotations

from importlib.resources import files
from typing import Any

from shotforge.comfyui.workflow_template import ComfyUIWorkflowTemplate


class ComfyUIWorkflowRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, tuple[str, dict[str, Any]]] = {}

    def register_resource(
        self,
        template_id: str,
        resource_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._templates[template_id] = (resource_name, metadata or {})

    def get(self, template_id: str) -> ComfyUIWorkflowTemplate:
        if template_id not in self._templates:
            available = ", ".join(self.list()) or "none"
            raise KeyError(f"Unknown ComfyUI workflow template: {template_id}. Available: {available}")
        resource_name, metadata = self._templates[template_id]
        text = files("shotforge.comfyui.workflows").joinpath(resource_name).read_text(encoding="utf-8")
        return ComfyUIWorkflowTemplate.from_json_text(template_id, text, metadata=metadata)

    def list(self) -> list[str]:
        return sorted(self._templates)


def build_workflow_registry() -> ComfyUIWorkflowRegistry:
    registry = ComfyUIWorkflowRegistry()
    registry.register_resource(
        "txt2img_sd15",
        "txt2img_sd15.json",
        metadata={
            "display_name": "SD 1.5 txt2img",
            "modality": "image",
            "status": "template_only",
        },
    )
    return registry
