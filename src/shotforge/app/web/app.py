from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from shotforge.core.capability_catalog import build_capability_catalog
from shotforge.config import get_settings
from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.project_state import OutputLanguage, ProjectState
from shotforge.core.version_manager import VersionManager
from shotforge.generators import build_default_generator_registry, build_generator_catalog
from shotforge.i18n import get_translator
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline
from shotforge.workflows.iterative_redesign_workflow import run_iterative_redesign

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))
app = FastAPI(title="ShotForge / 镜铸", version="0.1.0")


def _format_diff_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


templates.env.filters["diff_value"] = _format_diff_value


class RunRequest(BaseModel):
    idea: str = Field(min_length=2)
    style: str = "cinematic"
    language: OutputLanguage = "zh"
    duration_seconds: int = Field(default=24, ge=6, le=180)
    with_evaluation: bool = False
    with_planning: bool = False
    rubric_id: str = "baseline_v1"
    max_iterations: int = Field(default=3, ge=2, le=10)
    generator_provider_id: str = "mock"


class RunResponse(BaseModel):
    project_id: str
    run_id: str
    version: int
    exports: dict[str, str]
    state: ProjectState


class FormState(BaseModel):
    idea: str
    style: str = "cinematic"
    language: OutputLanguage = "zh"
    mode: str = "design"
    rubric_id: str = "baseline_v1"
    duration_seconds: int = 24
    max_iterations: int = 3
    generator_provider_id: str = "mock"


def _web_ui_labels(language: OutputLanguage) -> dict[str, str]:
    translator = get_translator()
    keys = {
        "header_subtitle": "web.header.subtitle",
        "form_title": "web.form.title",
        "form_idea": "web.form.idea",
        "form_default_idea": "web.form.default_idea",
        "form_style": "web.form.style",
        "form_language": "web.form.language",
        "form_language_zh": "web.form.language_zh",
        "form_language_en": "web.form.language_en",
        "form_mode": "web.form.mode",
        "form_mode_design": "web.form.mode_design",
        "form_mode_full_loop": "web.form.mode_full_loop",
        "form_mode_planning": "web.form.mode_planning",
        "form_rubric": "web.form.rubric",
        "form_duration": "web.form.duration",
        "form_max_iterations": "web.form.max_iterations",
        "form_generator_provider": "web.form.generator_provider",
        "form_submit": "web.form.submit",
        "run_title": "web.run.title",
        "run_scene": "web.run.scene",
        "run_issues": "web.run.issues",
        "run_ready_title": "web.run.ready_title",
        "run_ready_body": "web.run.ready_body",
        "exports_json": "web.exports.json",
        "exports_csv": "web.exports.csv",
        "exports_markdown": "web.exports.markdown",
        "exports_evaluation_csv": "web.exports.evaluation_csv",
        "exports_manifest": "web.exports.manifest",
        "exports_trace": "web.exports.trace",
        "exports_run_summary": "web.exports.run_summary",
        "solution_title": "web.solution.title",
        "solution_subtitle": "web.solution.subtitle",
        "solution_industry": "web.solution.industry",
        "solution_scenario": "web.solution.scenario",
        "solution_objective": "web.solution.objective",
        "solution_model_strategy": "web.solution.model_strategy",
        "solution_components": "web.solution.components",
        "solution_integrations": "web.solution.integrations",
        "solution_success": "web.solution.success",
        "solution_rollout": "web.solution.rollout",
        "solution_value": "web.solution.value",
        "solution_safety": "web.solution.safety",
        "solution_knowledge": "web.solution.knowledge",
        "solution_patterns": "web.solution.patterns",
        "solution_metrics": "web.solution.metrics",
        "readiness_title": "web.readiness.title",
        "readiness_subtitle": "web.readiness.subtitle",
        "readiness_overall": "web.readiness.overall",
        "readiness_checks": "web.readiness.checks",
        "readiness_handoff": "web.readiness.handoff",
        "readiness_next_actions": "web.readiness.next_actions",
        "readiness_risks": "web.readiness.risks",
        "readiness_required": "web.readiness.required",
        "readiness_remediation": "web.readiness.remediation",
        "evaluation_title": "web.evaluation.title",
        "evaluation_show_signals": "web.evaluation.show_signals",
        "correction_plans_title": "web.correction_plans.title",
        "correction_plans_version_preview": "web.correction_plans.version_preview",
        "correction_plans_priority": "web.correction_plans.priority",
        "correction_plans_risk": "web.correction_plans.risk",
        "correction_plans_affected_fields": "web.correction_plans.affected_fields",
        "correction_plans_target_issues": "web.correction_plans.target_issues",
        "correction_patches_title": "web.correction_patches.title",
        "correction_patches_agent": "web.correction_patches.agent",
        "correction_patches_expected_effect": "web.correction_patches.expected_effect",
        "correction_patches_operations": "web.correction_patches.operations",
        "correction_patches_rationale": "web.correction_patches.rationale",
        "version_diff_title": "web.version_diff.title",
        "version_diff_chain_title": "web.version_diff.chain_title",
        "version_diff_open": "web.version_diff.open",
        "version_diff_changed_shots": "web.version_diff.changed_shots",
        "version_diff_changed_prompts": "web.version_diff.changed_prompts",
        "version_diff_changed_audio_cues": "web.version_diff.changed_audio_cues",
        "version_diff_resolved_issues": "web.version_diff.resolved_issues",
        "version_diff_field_changes": "web.version_diff.field_changes",
        "version_diff_explanation": "web.version_diff.explanation",
        "version_diff_before": "web.version_diff.before",
        "version_diff_after": "web.version_diff.after",
        "version_diff_path": "web.version_diff.path",
        "version_diff_change_type": "web.version_diff.change_type",
        "version_diff_no_field_changes": "web.version_diff.no_field_changes",
        "convergence_title": "web.convergence.title",
        "convergence_overall_delta": "web.convergence.overall_delta",
        "convergence_status": "web.convergence.status",
        "convergence_resolved": "web.convergence.resolved",
        "convergence_remaining": "web.convergence.remaining",
        "convergence_new": "web.convergence.new",
        "convergence_dimensions": "web.convergence.dimensions",
        "convergence_history": "web.convergence.history",
        "convergence_stop_reason": "web.convergence.stop_reason",
        "snapshots_title": "web.snapshots.title",
        "snapshots_label": "web.snapshots.label",
        "snapshots_file": "web.snapshots.file",
        "verification_title": "web.verification.title",
        "verification_summary": "web.verification.summary",
        "verification_failed": "web.verification.failed",
        "verification_warnings": "web.verification.warnings",
        "signal_source_evaluators": "web.signal_source.evaluators",
        "signal_source_signals": "web.signal_source.signals",
        "signal_source_source": "web.signal_source.source",
        "signal_source_signal": "web.signal_source.signal",
        "signal_source_score": "web.signal_source.score",
        "signal_source_threshold": "web.signal_source.threshold",
        "harness_title": "web.harness.title",
        "harness_subtitle": "web.harness.subtitle",
        "harness_context": "web.harness.context",
        "harness_tools": "web.harness.tools",
        "harness_policy": "web.harness.policy",
        "harness_mcp": "web.harness.mcp",
        "harness_sandbox": "web.harness.sandbox",
        "harness_memory": "web.harness.memory",
        "harness_state": "web.harness.state",
        "harness_agent": "web.harness.agent",
        "harness_sources": "web.harness.sources",
        "harness_chars": "web.harness.chars",
        "harness_no_records": "web.harness.no_records",
        "harness_tool_status": "web.harness.tool_status",
        "harness_latency": "web.harness.latency",
        "harness_transitions": "web.harness.transitions",
        "harness_changed_fields": "web.harness.changed_fields",
        "harness_invariant_status": "web.harness.invariant_status",
        "harness_topology": "web.harness.topology",
        "harness_nodes": "web.harness.nodes",
        "harness_edges": "web.harness.edges",
    }
    return {name: translator.t(language, key) for name, key in keys.items()}


def _enum_labels(language: OutputLanguage, category: str, values: list[str]) -> dict[str, str]:
    translator = get_translator()
    return {
        value: translator.t(language, f"web.enums.{category}.{value}")
        for value in values
    }


def _version_snapshots(state: ProjectState | None) -> list[dict[str, str]]:
    if state is None:
        return []
    return VersionManager().list_snapshots(state.project_id)


def _available_generator_providers() -> list[dict[str, Any]]:
    registry = build_generator_catalog()
    providers = []
    for provider_id in registry.list(available_only=False):
        provider = registry.get(provider_id, require_available=False)
        providers.append(
            {
                "provider_id": provider.provider_id,
                "display_name": provider.display_name,
                "supports_real_generation": provider.supports_real_generation(),
                "available": registry.is_available(provider_id),
            }
        )
    return providers


def _harness_inspector(state: ProjectState | None) -> dict[str, Any]:
    return build_harness_audit(state)


def _validate_generator_provider_id(provider_id: str) -> str:
    try:
        build_default_generator_registry().get(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return provider_id


def _package_path(run_id: str) -> Path:
    return get_settings().runs_dir / run_id / "package.json"


def _load_run(run_id: str) -> ProjectState:
    path = _package_path(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return ProjectState.model_validate_json(path.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    run_id: str | None = None,
    language: OutputLanguage = "zh",
) -> HTMLResponse:
    state = _load_run(run_id) if run_id else None
    active_language = state.language if state else language
    translator = get_translator()
    form_state = FormState(
        idea=state.user_idea if state else translator.t(active_language, "web.form.default_idea"),
        style=state.style if state else "cinematic",
        language=active_language,
        mode=str(state.metadata.get("run_mode", "design")) if state else "design",
        rubric_id=str(state.metadata.get("rubric_id", "baseline_v1")) if state else "baseline_v1",
        duration_seconds=state.duration_seconds if state else 24,
        max_iterations=int(state.metadata.get("max_iterations", 3)) if state else 3,
        generator_provider_id=str(state.metadata.get("generator_provider_id", "mock"))
        if state
        else "mock",
    )
    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "state": state,
            "form_state": form_state,
            "ui": _web_ui_labels(active_language),
            "status_labels": _enum_labels(
                active_language,
                "convergence_status",
                ["improved", "mixed", "regressed", "unchanged"],
            ),
            "stop_reason_labels": _enum_labels(
                active_language,
                "stop_reason",
                [
                    "continue",
                    "no_re_evaluation_yet",
                    "design_package_unchanged",
                    "selected_iterations_reached",
                    "regression_detected",
                    "score_delta_below_threshold",
                    "all_tracked_issues_resolved",
                ],
            ),
            "change_type_labels": _enum_labels(
                active_language,
                "change_type",
                ["added", "removed", "modified"],
            ),
            "snapshots": _version_snapshots(state),
            "generator_providers": _available_generator_providers(),
            "harness_inspector": _harness_inspector(state),
        },
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/runs")
def create_run_form(
    idea: str = Form(...),
    style: str = Form("cinematic"),
    language: OutputLanguage = Form("zh"),
    duration_seconds: int = Form(24),
    mode: str = Form("design"),
    rubric_id: str = Form("baseline_v1"),
    max_iterations: int = Form(3),
    generator_provider_id: str = Form("mock"),
) -> RedirectResponse:
    generator_provider_id = _validate_generator_provider_id(generator_provider_id)
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
    state.metadata["run_mode"] = mode
    state.metadata["rubric_id"] = rubric_id
    state.metadata["max_iterations"] = max_iterations
    state.metadata["generator_provider_id"] = generator_provider_id
    from shotforge.exporters import ExportManager

    ExportManager().export_all(state)
    return RedirectResponse(url=f"/?run_id={state.run_id}", status_code=303)


@app.post("/api/runs", response_model=RunResponse)
def create_run(payload: RunRequest) -> RunResponse:
    generator_provider_id = _validate_generator_provider_id(payload.generator_provider_id)
    if payload.with_evaluation or payload.with_planning:
        state = run_full_loop_pipeline(
            idea=payload.idea,
            style=payload.style,
            duration_seconds=payload.duration_seconds,
            language=payload.language,
            rubric_id=payload.rubric_id,
            generator_provider_id=generator_provider_id,
        )
        if payload.with_planning:
            state = run_iterative_redesign(
                state,
                max_iterations=payload.max_iterations,
                generator_provider_id=generator_provider_id,
            )
            from shotforge.exporters import ExportManager

            ExportManager().export_all(state)
    else:
        state = run_design_pipeline(
            idea=payload.idea,
            style=payload.style,
            duration_seconds=payload.duration_seconds,
            language=payload.language,
        )
    return RunResponse(
        project_id=state.project_id,
        run_id=state.run_id,
        version=state.version,
        exports={artifact.format: artifact.path for artifact in state.exports},
        state=state,
    )


@app.get("/api/capabilities")
def get_capabilities() -> dict[str, Any]:
    return build_capability_catalog()


@app.get("/api/health")
def get_health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "storage": {
            "storage_root": str(settings.storage_root),
            "runs_dir": str(settings.runs_dir),
            "versions_dir": str(settings.versions_dir),
            "knowledge_base_path": str(settings.knowledge_base_path),
            "memory_store_path": str(settings.memory_store_path),
            "runs_dir_exists": settings.runs_dir.exists(),
            "versions_dir_exists": settings.versions_dir.exists(),
        },
    }


@app.get("/api/runs/{run_id}", response_model=ProjectState)
def get_run(run_id: str) -> ProjectState:
    return _load_run(run_id)


@app.get("/api/runs/{run_id}/trace")
def get_trace(run_id: str) -> list[dict]:
    return json.loads(_load_run(run_id).model_dump_json())["trace_logs"]


@app.get("/api/runs/{run_id}/harness")
def get_harness_audit(run_id: str) -> dict[str, Any]:
    return build_harness_audit(_load_run(run_id))


@app.get("/api/runs/{run_id}/readiness")
def get_readiness(run_id: str) -> dict[str, Any]:
    state = _load_run(run_id)
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


@app.get("/api/runs/{run_id}/versions")
def get_versions(run_id: str) -> list[dict[str, str]]:
    state = _load_run(run_id)
    return VersionManager().list_snapshots(state.project_id)


@app.get("/api/runs/{run_id}/export/{export_format}")
def download_export(run_id: str, export_format: str) -> FileResponse:
    mapping = {
        "json": ("package.json", "application/json"),
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

__all__ = ["app"]
