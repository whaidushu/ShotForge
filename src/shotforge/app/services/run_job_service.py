from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from shotforge.config import get_settings
from shotforge.core.project_state import ProjectState

RunJobState = Literal["queued", "running", "completed", "failed", "unknown"]

STEP_LABELS = {
    "design": "Design",
    "generate": "Generate",
    "observe": "Observe",
    "evaluate": "Evaluate",
    "optimize": "Optimize",
    "export": "Export",
}

EXPECTED_STEPS_BY_MODE = {
    "design": ["design", "export"],
    "full_loop": ["design", "generate", "observe", "evaluate", "export"],
    "planning": ["design", "generate", "observe", "evaluate", "optimize", "export"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def expected_steps_for_mode(mode: str | None) -> list[str]:
    return list(EXPECTED_STEPS_BY_MODE.get(mode or "", EXPECTED_STEPS_BY_MODE["full_loop"]))


def completed_steps_for_state(state: ProjectState) -> list[str]:
    steps = ["design"]
    if state.generation_results:
        steps.append("generate")
    if state.observation_reports:
        steps.append("observe")
    if state.evaluation_reports:
        steps.append("evaluate")
    if state.version > 1 or state.redesign_plans:
        steps.append("optimize")
    if state.exports:
        steps.append("export")
    return steps


class RunJobStatus(BaseModel):
    run_id: str
    status: RunJobState = "unknown"
    mode: str = ""
    percent: int = 0
    current_step: str = ""
    completed_steps: list[str] = Field(default_factory=list)
    total_steps: int = 5
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunJobService:
    def status_path(self, run_id: str):
        return get_settings().runs_dir / run_id / "job_status.json"

    def record_completed(self, state: ProjectState, *, mode: str) -> RunJobStatus:
        steps = completed_steps_for_state(state)
        expected_steps = expected_steps_for_mode(mode)
        status = RunJobStatus(
            run_id=state.run_id,
            status="completed",
            mode=mode,
            percent=100,
            current_step="completed",
            completed_steps=steps,
            total_steps=len(expected_steps),
            metadata={
                "project_id": state.project_id,
                "version": state.version,
                "generator_provider_id": state.metadata.get("generator_provider_id", ""),
                "provider_profile_id": state.metadata.get("provider_profile_id", ""),
            },
        )
        return self._write(status)

    def record_failed(self, run_id: str, *, mode: str, error: str) -> RunJobStatus:
        status = RunJobStatus(
            run_id=run_id,
            status="failed",
            mode=mode,
            percent=0,
            current_step="failed",
            error=error,
        )
        return self._write(status)

    def get_status(self, run_id: str) -> RunJobStatus:
        path = self.status_path(run_id)
        if path.exists():
            status = RunJobStatus.model_validate_json(path.read_text(encoding="utf-8"))
            if status.status == "completed":
                expected_steps = expected_steps_for_mode(status.mode)
                if status.total_steps != len(expected_steps) or status.percent != 100:
                    status.total_steps = len(expected_steps)
                    status.percent = 100
                    status.current_step = "completed"
                    return self._write(status)
            return status
        package_path = get_settings().runs_dir / run_id / "package.json"
        if package_path.exists():
            state = ProjectState.model_validate_json(package_path.read_text(encoding="utf-8"))
            return self.record_completed(state, mode=state.metadata.get("run_mode", ""))
        return RunJobStatus(run_id=run_id, status="unknown", current_step="not_found")

    def _write(self, status: RunJobStatus) -> RunJobStatus:
        status.updated_at = _now_iso()
        path = self.status_path(status.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(status.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return status
