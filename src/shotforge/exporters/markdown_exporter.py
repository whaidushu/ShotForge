from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from shotforge.core.project_state import ExportArtifact, ProjectState
from shotforge.l10n import t


def export_markdown(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "package.md"
    env = Environment(
        loader=PackageLoader("shotforge", "templates"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("package.md.j2")
    path.write_text(
        template.render(state=state, labels=t(state.language, "md")),
        encoding="utf-8",
    )
    _record(state, "markdown", path)
    return path


def _record(state: ProjectState, export_format: str, path: Path) -> None:
    state.exports = [item for item in state.exports if item.format != export_format]
    state.exports.append(ExportArtifact(format=export_format, path=str(path)))
    state.touch()
