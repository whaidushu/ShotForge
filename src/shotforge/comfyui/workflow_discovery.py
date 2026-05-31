from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal


WorkflowFormat = Literal["api", "ui_graph", "unknown"]


@dataclass(frozen=True)
class ComfyUIWorkflowInfo:
    workflow_id: str
    name: str
    path: Path | None
    source: str
    format: WorkflowFormat
    callable: bool
    node_count: int
    metadata: dict[str, Any]


def default_user_workflows_dir() -> Path:
    return Path.home() / "Documents" / "ComfyUI" / "user" / "default" / "workflows"


def workflow_id_from_path(path: Path, root: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    return "local:" + "/".join(relative.parts)


def inspect_workflow_json(data: Any) -> tuple[WorkflowFormat, int]:
    if not isinstance(data, dict):
        return "unknown", 0
    if "nodes" in data and isinstance(data.get("nodes"), list):
        return "ui_graph", len(data["nodes"])
    if data and all(isinstance(node, dict) and "class_type" in node for node in data.values()):
        return "api", len(data)
    return "unknown", 0


def discover_local_workflows(root: Path) -> list[ComfyUIWorkflowInfo]:
    if not root.exists():
        return []
    workflows: list[ComfyUIWorkflowInfo] = []
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            workflow_format, node_count = inspect_workflow_json(data)
            metadata: dict[str, Any] = {}
        except Exception as exc:
            workflow_format = "unknown"
            node_count = 0
            metadata = {"error": str(exc)}
        workflows.append(
            ComfyUIWorkflowInfo(
                workflow_id=workflow_id_from_path(path, root),
                name=path.stem,
                path=path,
                source="local",
                format=workflow_format,
                callable=workflow_format == "api",
                node_count=node_count,
                metadata=metadata,
            )
        )
    return workflows
