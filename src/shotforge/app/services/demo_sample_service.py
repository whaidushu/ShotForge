from __future__ import annotations

import json
import shutil
from pathlib import Path

from shotforge.config import get_settings
from shotforge.core.project_state import OutputLanguage


class DemoSampleService:
    sample_run_ids: dict[OutputLanguage, str] = {
        "en": "shotforge_gold_sample",
        "zh": "shotforge_gold_sample_zh",
    }

    def __init__(
        self,
        *,
        sample_dir: Path | None = None,
        runs_dir: Path | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        self.demo_runs_dir = repo_root / "examples" / "demo_runs"
        self.sample_dir = sample_dir
        self.runs_dir = runs_dir

    def sample_run_id(self, language: OutputLanguage) -> str:
        return self.sample_run_ids[language]

    def seed(self, *, language: OutputLanguage = "en", force: bool = False) -> str:
        run_id = self.sample_run_id(language)
        source = (self.sample_dir or self.demo_runs_dir / run_id).resolve()
        runs_dir = (self.runs_dir or get_settings().runs_dir).resolve()
        target = runs_dir / run_id
        if not (source / "package.json").exists():
            raise FileNotFoundError(f"Demo sample package not found: {source / 'package.json'}")
        if target.exists() and force:
            shutil.rmtree(target)
        if not (target / "package.json").exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, target, dirs_exist_ok=True)
            self._rewrite_export_paths(target, run_id)
        return run_id

    def _rewrite_export_paths(self, target_dir: Path, run_id: str) -> None:
        package_path = target_dir / "package.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        package["run_id"] = run_id
        for export in package.get("exports", []):
            filename = self._filename_for_export(str(export.get("format", "")))
            if filename:
                export["path"] = str(target_dir / filename)
        package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _filename_for_export(export_format: str) -> str:
        return {
            "json": "package.json",
            "csv": "package.csv",
            "markdown": "package.md",
            "evaluation_csv": "evaluation.csv",
            "manifest": "manifest.json",
            "package_view": "package_view.json",
            "trace": "trace.json",
            "run_summary": "run_summary.md",
        }.get(export_format, "")
