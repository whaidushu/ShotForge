from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from shotforge.app.api.schemas import RunRequest, RunResponse
from shotforge.app.errors import runtime_error_payload
from shotforge.app.services.artifact_service import ArtifactNotFoundError, ArtifactService
from shotforge.app.services.run_service import RunService
from shotforge.app.services.run_status_service import RunStatusService
from shotforge.config import get_settings
from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.packages import ProjectPackageView
from shotforge.core.project_state import ProjectState
from shotforge.core.version_manager import VersionManager
from shotforge.workflows.effect_demo_workflow import load_effect_comparison


def build_run_router(run_service: RunService, artifact_service: ArtifactService) -> APIRouter:
    router = APIRouter(prefix="/api/runs", tags=["runs"])
    run_status_service = RunStatusService()

    def load_run(run_id: str) -> ProjectState:
        try:
            return run_service.load_run(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("", response_model=RunResponse)
    def create_run(payload: RunRequest) -> RunResponse:
        try:
            state = run_service.create_run_from_payload(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail=runtime_error_payload(exc)) from exc
        return RunResponse(
            project_id=state.project_id,
            run_id=state.run_id,
            version=state.version,
            exports={artifact.format: artifact.path for artifact in state.exports},
            state=state,
        )

    @router.get("")
    def list_runs(limit: int = 20) -> dict[str, Any]:
        return {"runs": run_service.list_run_history(limit=limit)}

    @router.get("/dashboard")
    def get_run_dashboard(limit: int = 40) -> dict[str, Any]:
        return run_status_service.dashboard(limit=limit).model_dump(mode="json")

    @router.get("/{run_id}", response_model=ProjectState)
    def get_run(run_id: str) -> ProjectState:
        return load_run(run_id)

    @router.get("/{run_id}/package-view")
    def get_package_view(run_id: str) -> dict[str, Any]:
        return ProjectPackageView.from_state(load_run(run_id)).model_dump(mode="json")

    @router.get("/{run_id}/status")
    def get_run_status(run_id: str) -> dict[str, Any]:
        status = run_service.run_job_service.get_status(run_id)
        if status.status == "unknown" and status.current_step == "not_found":
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        return status.model_dump(mode="json")

    @router.get("/{run_id}/trace")
    def get_trace(run_id: str) -> list[dict]:
        return json.loads(load_run(run_id).model_dump_json())["trace_logs"]

    @router.get("/{run_id}/harness")
    def get_harness_audit(run_id: str) -> dict[str, Any]:
        return build_harness_audit(load_run(run_id))

    @router.get("/{run_id}/runtime-evidence")
    def get_runtime_evidence(run_id: str) -> dict[str, Any]:
        return build_harness_audit(load_run(run_id))

    @router.get("/{run_id}/workbench")
    def get_run_workbench(run_id: str) -> dict[str, Any]:
        return run_status_service.workbench(load_run(run_id)).model_dump(mode="json")

    @router.get("/{run_id}/generation-artifacts")
    def get_generation_artifacts(run_id: str) -> list[dict[str, Any]]:
        return artifact_service.generation_artifacts(load_run(run_id))

    @router.get("/{run_id}/effect-comparison")
    def get_effect_comparison(run_id: str) -> dict[str, Any]:
        load_run(run_id)
        try:
            return load_effect_comparison(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{run_id}/artifacts/{artifact_kind}/{iteration}/{shot_id}")
    def download_generation_artifact(
        run_id: str,
        artifact_kind: str,
        iteration: str,
        shot_id: str,
    ) -> FileResponse:
        try:
            path = artifact_service.artifact_path_from_state(
                load_run(run_id), artifact_kind, iteration, shot_id
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ArtifactNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        media_type = {
            "video": "video/mp4",
            "prompt": "text/plain",
            "prompt_json": "application/json",
            "workflow": "application/json",
        }[artifact_kind]
        return FileResponse(path, media_type=media_type, filename=path.name)

    @router.get("/{run_id}/readiness")
    def get_readiness(run_id: str) -> dict[str, Any]:
        state = load_run(run_id)
        if state.delivery_readiness is None:
            raise HTTPException(status_code=404, detail=f"Readiness report not found: {run_id}")
        report = state.delivery_readiness
        return {
            "project_id": state.project_id,
            "run_id": state.run_id,
            "overall_status": report.overall_status,
            "checks": [item.model_dump(mode="json") for item in report.checks],
            "summary": {
                "passed": len([item for item in report.checks if item.status == "passed"]),
                "warnings": len([item for item in report.checks if item.status == "warning"]),
                "failed": len([item for item in report.checks if item.status == "failed"]),
            },
            "handoff_deliverables": report.handoff_deliverables,
            "next_actions": report.next_actions,
            "risk_register": report.risk_register,
        }

    @router.get("/{run_id}/versions")
    def get_versions(run_id: str) -> list[dict[str, str]]:
        state = load_run(run_id)
        return VersionManager().list_snapshots(state.project_id)

    @router.get("/{run_id}/export/{export_format}")
    def download_export(run_id: str, export_format: str) -> FileResponse:
        mapping = {
            "json": ("package.json", "application/json"),
            "package_view": ("package_view.json", "application/json"),
            "csv": ("package.csv", "text/csv"),
            "markdown": ("package.md", "text/markdown"),
            "md": ("package.md", "text/markdown"),
            "manifest": ("manifest.json", "application/json"),
            "trace": ("trace.json", "application/json"),
            "run_summary": ("run_summary.md", "text/markdown"),
            "summary": ("run_summary.md", "text/markdown"),
            "evaluation_csv": ("evaluation.csv", "text/csv"),
            "evaluation": ("evaluation.csv", "text/csv"),
        }
        if export_format not in mapping:
            raise HTTPException(status_code=400, detail="export_format must be json, csv, or markdown")
        filename, media_type = mapping[export_format]
        path = get_settings().runs_dir / run_id / filename
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Export not found: {export_format}")
        return FileResponse(path, media_type=media_type, filename=filename)

    return router
