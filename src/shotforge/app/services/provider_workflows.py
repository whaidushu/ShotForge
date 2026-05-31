from __future__ import annotations

from pathlib import Path
from typing import Any

from shotforge.comfyui import build_workflow_registry, discover_local_workflows
from shotforge.config import get_settings


class ComfyUIWorkflowService:
    def available_workflows(self, root: str | None = None) -> list[dict[str, Any]]:
        return self.workflow_status(root=root)["workflows"]

    def workflow_status(self, root: str | None = None) -> dict[str, Any]:
        settings = get_settings()
        warnings: list[dict[str, str]] = []
        workflows: list[dict[str, Any]] = []
        try:
            registry = build_workflow_registry()
            workflows = [self.workflow_info_to_dict(item) for item in registry.describe()]
        except Exception as exc:
            warnings.append(
                {
                    "check_id": "comfyui_workflow_registry",
                    "status": "warning",
                    "detail": f"Built-in workflow registry is unavailable: {exc}",
                }
            )
        seen = {item["workflow_id"] for item in workflows}
        workflow_root = root or settings.comfyui_workflows_dir
        if workflow_root:
            root_path = Path(workflow_root)
            if not root_path.exists():
                warnings.append(
                    {
                        "check_id": "comfyui_workflows_dir",
                        "status": "warning",
                        "detail": f"Workflow folder not found: {root_path}",
                    }
                )
            else:
                try:
                    for item in discover_local_workflows(root_path):
                        if item.workflow_id in seen:
                            continue
                        workflows.append(self.workflow_info_to_dict(item))
                        seen.add(item.workflow_id)
                except Exception as exc:
                    warnings.append(
                        {
                            "check_id": "comfyui_workflow_discovery",
                            "status": "warning",
                            "detail": f"Local workflow discovery failed: {exc}",
                        }
                    )
        return {"workflows": workflows, "warnings": warnings}

    @staticmethod
    def workflow_info_to_dict(item: Any) -> dict[str, Any]:
        return {
            "workflow_id": item.workflow_id,
            "name": item.name,
            "path": str(item.path) if item.path else "",
            "source": item.source,
            "format": item.format,
            "callable": item.callable,
            "node_count": item.node_count,
            "metadata": item.metadata,
        }
