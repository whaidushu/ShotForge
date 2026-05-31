from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shotforge.app.services.provider_profiles import ProviderProfile, ProviderProfileStore
from shotforge.app.services.provider_service import ProviderService
from shotforge.app.services.run_job_service import (
    STEP_LABELS,
    RunJobService,
    completed_steps_for_state,
    expected_steps_for_mode,
)
from shotforge.config import get_settings
from shotforge.core.project_state import OutputLanguage, ProjectState
from shotforge.core.version_manager import VersionManager
from shotforge.exporters import ExportManager
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline
from shotforge.workflows.iterative_redesign_workflow import run_iterative_redesign


class RunService:
    def __init__(
        self,
        provider_service: ProviderService | None = None,
        run_job_service: RunJobService | None = None,
    ) -> None:
        self.provider_service = provider_service or ProviderService()
        self.run_job_service = run_job_service or RunJobService()

    def create_run(
        self,
        *,
        idea: str,
        style: str,
        duration_seconds: int,
        language: OutputLanguage,
        mode: str,
        rubric_id: str,
        max_iterations: int,
        profile: ProviderProfile,
        persist_profile: bool = True,
    ) -> ProjectState:
        generator_provider_id = self.provider_service.validate_generator_provider_id(
            profile.generator_provider_id
        )
        profile.generator_provider_id = generator_provider_id
        if persist_profile:
            profile = ProviderProfileStore().upsert(profile)
        with self.provider_service.scoped_provider_profile(profile):
            if mode in {"full_loop", "planning"}:
                state = run_full_loop_pipeline(
                    idea=idea,
                    style=style,
                    duration_seconds=duration_seconds,
                    language=language,
                    rubric_id=rubric_id,
                    generator_provider_id=generator_provider_id,
                )
                if mode == "planning":
                    state = run_iterative_redesign(
                        state,
                        max_iterations=max_iterations,
                        generator_provider_id=generator_provider_id,
                    )
            else:
                state = run_design_pipeline(
                    idea=idea,
                    style=style,
                    duration_seconds=duration_seconds,
                    language=language,
                )
            self.provider_service.record_provider_config_metadata(state)
        state.metadata["run_mode"] = mode
        state.metadata["rubric_id"] = rubric_id
        state.metadata["max_iterations"] = max_iterations
        state.metadata["generator_provider_id"] = generator_provider_id
        self.provider_service.record_provider_profile_metadata(state, profile)
        ExportManager().export_all(state)
        self.run_job_service.record_completed(state, mode=mode)
        return state

    def create_run_from_payload(self, payload: Any) -> ProjectState:
        profile = self.provider_service.profile_from_payload(payload)
        return self.create_run(
            idea=payload.idea,
            style=payload.style,
            duration_seconds=payload.duration_seconds,
            language=payload.language,
            mode="planning" if payload.with_planning else "full_loop" if payload.with_evaluation else "design",
            rubric_id=payload.rubric_id,
            max_iterations=payload.max_iterations,
            profile=profile,
            persist_profile=True,
        )

    def package_path(self, run_id: str) -> Path:
        return get_settings().runs_dir / run_id / "package.json"

    def load_run(self, run_id: str) -> ProjectState:
        path = self.package_path(run_id)
        if not path.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        return ProjectState.model_validate_json(path.read_text(encoding="utf-8"))

    def list_run_history(self, limit: int = 20) -> list[dict[str, Any]]:
        runs_dir = get_settings().runs_dir
        if not runs_dir.exists():
            return []
        history: list[dict[str, Any]] = []
        package_paths = sorted(
            runs_dir.glob("*/package.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in package_paths[:limit]:
            try:
                state = ProjectState.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            latest_score = None
            if state.evaluation_reports:
                latest_score = state.evaluation_reports[-1].score_card.overall_score
            history.append(
                {
                    "run_id": state.run_id,
                    "project_id": state.project_id,
                    "idea": state.user_idea,
                    "language": state.language,
                    "mode": state.metadata.get("run_mode", "design"),
                    "generator_provider_id": state.metadata.get(
                        "generator_provider_id", state.prompt_package.provider
                    ),
                    "provider_profile_name": state.metadata.get("provider_profile_name", ""),
                    "version": state.version,
                    "latest_score": latest_score,
                    "updated_at": path.stat().st_mtime,
                }
            )
        return history

    @staticmethod
    def version_snapshots(state: ProjectState | None) -> list[dict[str, str]]:
        if state is None:
            return []
        return VersionManager().list_snapshots(state.project_id)

    @staticmethod
    def run_progress(state: ProjectState | None) -> dict[str, Any]:
        mode = str(state.metadata.get("run_mode", "design")) if state else "full_loop"
        completed = set(completed_steps_for_state(state)) if state else set()
        steps = [
            {"id": step_id, "label": STEP_LABELS[step_id], "done": step_id in completed}
            for step_id in expected_steps_for_mode(mode)
        ]
        done_count = len([step for step in steps if step["done"]])
        return {
            "mode": mode,
            "steps": steps,
            "done_count": done_count,
            "total": len(steps),
            "percent": round(done_count / len(steps) * 100) if steps else 0,
        }

    def prompt_change_cards(self, state: ProjectState | None) -> list[dict[str, Any]]:
        if state is None:
            return []
        cards: list[dict[str, Any]] = []
        for diff in state.version_diffs:
            for change in diff.field_changes:
                path = str(change.path)
                if "prompt" not in path.lower() and "structured_template" not in path.lower():
                    continue
                cards.append(
                    {
                        "version": f"v{diff.from_version} -> v{diff.to_version}",
                        "path": path,
                        "change_type": change.change_type,
                        "before": self.format_diff_value(change.before),
                        "after": self.format_diff_value(change.after),
                        "explanation": diff.explanation,
                    }
                )
        if cards:
            return cards
        if state.prompt_package.prompts:
            return [
                {
                    "version": f"v{state.version}",
                    "path": prompt.shot_id,
                    "change_type": "current",
                    "before": "",
                    "after": prompt.prompt,
                    "explanation": "Current prompt package",
                }
                for prompt in state.prompt_package.prompts[:4]
            ]
        return []

    @staticmethod
    def format_diff_value(value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2)
