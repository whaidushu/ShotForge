from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from shotforge.config import get_settings
from shotforge.core.project_state import ProjectState


class VersionManager:
    def __init__(self, root: Path | None = None):
        self.root = root or get_settings().versions_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, state: ProjectState, label: str | None = None) -> Path:
        project_dir = self.root / state.project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"-{label}" if label else ""
        path = project_dir / f"v{state.version:03d}{suffix}.json"
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        state.versions.append(str(path))
        state.touch()
        return path

    def next_version(self, state: ProjectState) -> ProjectState:
        state.version += 1
        state.touch()
        return state

    def fork_next_version(self, state: ProjectState, reason: str = "redesign") -> ProjectState:
        next_state = deepcopy(state)
        next_state.version = state.version + 1
        next_state.exports = []
        next_state.trace_logs = []
        next_state.metadata["parent_version"] = state.version
        next_state.metadata["fork_reason"] = reason
        next_state.touch()
        return next_state

    def load_snapshot(self, project_id: str, version: int) -> ProjectState:
        path = self.root / project_id / f"v{version:03d}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProjectState.model_validate(data)

    def list_snapshots(self, project_id: str) -> list[dict[str, str]]:
        project_dir = self.root / project_id
        if not project_dir.exists():
            return []
        snapshots = []
        for path in sorted(project_dir.glob("v*.json")):
            snapshots.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "version": path.stem.split("-", 1)[0].removeprefix("v"),
                    "label": path.stem.split("-", 1)[1] if "-" in path.stem else "",
                }
            )
        return snapshots

__all__ = ["VersionManager"]
