from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

from shotforge.comfyui.workflow_discovery import (
    ComfyUIWorkflowInfo,
    default_user_workflows_dir,
    discover_local_workflows,
    inspect_workflow_json,
)
from shotforge.comfyui.workflow_template import ComfyUIWorkflowTemplate
from shotforge.config import get_settings


class ComfyUIWorkflowRegistry:
    def __init__(self) -> None:
        self._resource_templates: dict[str, tuple[str, dict[str, Any]]] = {}
        self._file_templates: dict[str, tuple[Path, dict[str, Any]]] = {}

    def register_resource(
        self,
        template_id: str,
        resource_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._resource_templates[template_id] = (resource_name, metadata or {})

    def register_file(
        self,
        template_id: str,
        path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._file_templates[template_id] = (path, metadata or {})

    def get(self, template_id: str) -> ComfyUIWorkflowTemplate:
        if template_id.startswith("file:"):
            return self._get_file_path(Path(template_id.removeprefix("file:")), template_id)
        if template_id in self._file_templates:
            path, metadata = self._file_templates[template_id]
            return self._get_file_path(path, template_id, metadata=metadata)
        if template_id not in self._resource_templates:
            available = ", ".join(self.list()) or "none"
            raise KeyError(f"Unknown ComfyUI workflow template: {template_id}. Available: {available}")
        resource_name, metadata = self._resource_templates[template_id]
        text = files("shotforge.comfyui.workflows").joinpath(resource_name).read_text(encoding="utf-8")
        return ComfyUIWorkflowTemplate.from_json_text(template_id, text, metadata=metadata)

    def list(self) -> list[str]:
        return sorted([*self._resource_templates, *self._file_templates])

    def describe(self) -> list[ComfyUIWorkflowInfo]:
        items: list[ComfyUIWorkflowInfo] = []
        for template_id, (resource_name, metadata) in self._resource_templates.items():
            template = self.get(template_id)
            workflow_format, node_count = inspect_workflow_json(template.workflow)
            items.append(
                ComfyUIWorkflowInfo(
                    workflow_id=template_id,
                    name=str(metadata.get("display_name", template_id)),
                    path=None,
                    source=f"resource:{resource_name}",
                    format=workflow_format,
                    callable=workflow_format == "api",
                    node_count=node_count,
                    metadata=metadata,
                )
            )
        for template_id, (path, metadata) in self._file_templates.items():
            try:
                workflow_format, node_count = inspect_workflow_json(
                    ComfyUIWorkflowTemplate.from_json_text(
                        template_id,
                        path.read_text(encoding="utf-8"),
                        metadata=metadata,
                    ).workflow
                )
            except Exception as exc:
                workflow_format = "unknown"
                node_count = 0
                metadata = {**metadata, "error": str(exc)}
            items.append(
                ComfyUIWorkflowInfo(
                    workflow_id=template_id,
                    name=path.stem,
                    path=path,
                    source="local",
                    format=workflow_format,
                    callable=workflow_format == "api",
                    node_count=node_count,
                    metadata=metadata,
                )
            )
        return sorted(items, key=lambda item: item.workflow_id)

    def _get_file_path(
        self,
        path: Path,
        template_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> ComfyUIWorkflowTemplate:
        text = path.read_text(encoding="utf-8")
        template = ComfyUIWorkflowTemplate.from_json_text(template_id, text, metadata=metadata)
        workflow_format, _ = inspect_workflow_json(template.workflow)
        if workflow_format != "api":
            raise ValueError(
                f"ComfyUI workflow {template_id} is {workflow_format}, not API format. "
                "Export it from ComfyUI with API format enabled before calling it."
            )
        return template


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
    registry.register_resource(
        "wan2_2_i2v_empty_start",
        "wan2_2_i2v_empty_start.json",
        metadata={
            "display_name": "Wan 2.2 image-to-video from generated start frame",
            "modality": "video",
            "status": "local_real",
        },
    )
    registry.register_resource(
        "wan2_2_ti2v_5b",
        "wan2_2_ti2v_5b.json",
        metadata={
            "display_name": "Wan 2.2 TI2V 5B text-to-video",
            "modality": "video",
            "status": "local_real",
        },
    )
    settings = get_settings()
    workflow_root = (
        Path(settings.comfyui_workflows_dir)
        if settings.comfyui_workflows_dir
        else default_user_workflows_dir()
    )
    for item in discover_local_workflows(workflow_root):
        registry.register_file(
            item.workflow_id,
            item.path or workflow_root,
            metadata={
                "display_name": item.name,
                "source": item.source,
                "format": item.format,
                "callable": item.callable,
                "node_count": item.node_count,
                "root": str(workflow_root),
            },
        )
    return registry
