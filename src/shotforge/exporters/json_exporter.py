from __future__ import annotations

import json
from pathlib import Path

from shotforge.core.packages import ProjectPackageView
from shotforge.core.project_state import ExportArtifact, ProjectState


def export_json(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "package.json"
    path.write_text(
        json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _record(state, "json", path)
    return path


def export_package_view(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "package_view.json"
    path.write_text(
        json.dumps(ProjectPackageView.from_state(state).model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _record(state, "package_view", path)
    return path


def _record(state: ProjectState, export_format: str, path: Path) -> None:
    state.exports = [item for item in state.exports if item.format != export_format]
    state.exports.append(ExportArtifact(format=export_format, path=str(path)))
    state.touch()
