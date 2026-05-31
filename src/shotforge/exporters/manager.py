from __future__ import annotations

from pathlib import Path

from shotforge.core.project_state import ProjectState
from shotforge.exporters.csv_exporter import export_csv
from shotforge.exporters.evaluation_csv_exporter import export_evaluation_csv
from shotforge.exporters.handoff_exporter import export_manifest, export_run_summary, export_trace
from shotforge.exporters.json_exporter import export_json, export_package_view
from shotforge.exporters.markdown_exporter import export_markdown
from shotforge.exporters.mp4_exporter import MP4Exporter


class ExportManager:
    def __init__(self, runs_dir: Path | None = None):
        from shotforge.config import get_settings

        self.runs_dir = runs_dir or get_settings().runs_dir

    def run_dir(self, state: ProjectState) -> Path:
        if not state.exports and "parent_version" not in state.metadata:
            state.run_id = self._unique_run_id(state.run_id)
        path = self.runs_dir / state.run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def export_json(self, state: ProjectState) -> Path:
        return export_json(state, self.run_dir(state))

    def export_package_view(self, state: ProjectState) -> Path:
        return export_package_view(state, self.run_dir(state))

    def export_csv(self, state: ProjectState) -> Path:
        return export_csv(state, self.run_dir(state))

    def export_markdown(self, state: ProjectState) -> Path:
        return export_markdown(state, self.run_dir(state))

    def export_evaluation_csv(self, state: ProjectState) -> Path:
        return export_evaluation_csv(state, self.run_dir(state))

    def export_manifest(self, state: ProjectState) -> Path:
        return export_manifest(state, self.run_dir(state))

    def export_trace(self, state: ProjectState) -> Path:
        return export_trace(state, self.run_dir(state))

    def export_run_summary(self, state: ProjectState) -> Path:
        return export_run_summary(state, self.run_dir(state))

    def export_mp4(
        self,
        state: ProjectState,
        *,
        aspect_ratio: str = "16:9",
        fps: int = 24,
        crf: int = 23,
    ) -> Path:
        return MP4Exporter().export(state, aspect_ratio=aspect_ratio, fps=fps, crf=crf)

    def export_all(self, state: ProjectState) -> list[Path]:
        paths = [
            self.export_csv(state),
            self.export_markdown(state),
        ]
        if state.evaluation_reports:
            paths.append(self.export_evaluation_csv(state))
        paths.extend(
            [
                self.export_manifest(state),
                self.export_trace(state),
                self.export_run_summary(state),
                self.export_package_view(state),
                self.export_json(state),
            ]
        )
        return paths

    def _unique_run_id(self, run_id: str) -> str:
        path = self.runs_dir / run_id
        if not path.exists() or not any(path.iterdir()):
            return run_id

        index = 2
        while True:
            candidate = f"{run_id}_{index:02d}"
            candidate_path = self.runs_dir / candidate
            if not candidate_path.exists() or not any(candidate_path.iterdir()):
                return candidate
            index += 1
