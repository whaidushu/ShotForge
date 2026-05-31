from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from shotforge.app.api.providers import build_provider_router
from shotforge.app.api.runs import build_run_router
from shotforge.app.api.system import build_system_router
from shotforge.app.errors import runtime_error_payload
from shotforge.app.services.artifact_service import ArtifactService
from shotforge.app.services.provider_service import ProviderService
from shotforge.app.services.run_service import RunService
from shotforge.comfyui import default_user_workflows_dir
from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.project_state import OutputLanguage, ProjectState
from shotforge.i18n import get_translator

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))
app = FastAPI(title="ShotForge / 镜铸", version="0.1.0")
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)
provider_service = ProviderService()
run_service = RunService(provider_service=provider_service)
artifact_service = ArtifactService()
app.include_router(build_run_router(run_service, artifact_service))
app.include_router(build_provider_router(provider_service))
app.include_router(build_system_router())


def _format_diff_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


templates.env.filters["diff_value"] = _format_diff_value


class FormState(BaseModel):
    idea: str
    style: str = "cinematic"
    language: OutputLanguage = "zh"
    mode: str = "design"
    rubric_id: str = "baseline_v1"
    duration_seconds: int = 24
    max_iterations: int = 3
    provider_profile_id: str = "local-real"
    provider_profile_name: str = "Local real generation"
    generator_provider_id: str = "comfyui"
    llm_provider_id: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = ""
    llm_api_key: str = ""
    evaluator_mode: str = "llm"
    comfyui_base_url: str = ""
    comfyui_workflows_dir: str = ""
    comfyui_workflow_id: str = "wan2_2_i2v_empty_start"
    comfyui_width: int = 320
    comfyui_height: int = 320
    comfyui_length: int = 9
    comfyui_fps: float = 8.0
    comfyui_max_shots: int = 0
    observer_provider_id: str = "prompt-proxy"
    vlm_model: str = ""
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    vlm_frame_sample_count: int = 4
    vlm_confidence_threshold: float = 0.65
    vlm_require_json: bool = True


def _web_ui_labels(language: OutputLanguage) -> dict[str, str]:
    translator = get_translator()
    keys = {
        "header_subtitle": "web.header.subtitle",
        "nav_workflow": "web.nav.workflow",
        "nav_config": "web.nav.config",
        "config_title": "web.config.title",
        "config_subtitle": "web.config.subtitle",
        "profile_label": "web.profile.label",
        "profile_name": "web.profile.name",
        "profile_save": "web.profile.save",
        "profile_preflight": "web.profile.preflight",
        "profile_test_chain": "web.profile.test_chain",
        "profile_test_chain_running": "web.profile.test_chain_running",
        "profile_test_chain_label": "web.profile.test_chain_label",
        "profile_test_chain_passed": "web.profile.test_chain_passed",
        "profile_back": "web.profile.back_to_workflow",
        "profile_default": "web.profile.default_name",
        "profile_saved": "web.profile.saved",
        "profile_checking": "web.profile.checking",
        "profile_check_label": "web.profile.check_label",
        "recent_runs": "web.recent_runs.title",
        "kpi_profile": "web.kpi.profile",
        "kpi_mode": "web.kpi.mode",
        "kpi_video": "web.kpi.video",
        "kpi_progress": "web.kpi.progress",
        "assets_count": "web.assets.count",
        "prompt_changes_title": "web.prompt_changes.title",
        "empty_video_title": "web.empty.video_title",
        "empty_video_body": "web.empty.video_body",
        "empty_prompt_title": "web.empty.prompt_title",
        "empty_prompt_body": "web.empty.prompt_body",
        "storyboard_title": "web.storyboard.title",
        "js_running": "web.js.running",
        "js_disabled": "web.js.disabled",
        "js_local": "web.js.local",
        "js_callable": "web.js.callable",
        "provider_config_required": "web.provider_state.config_required",
        "provider_unavailable": "web.provider_state.unavailable",
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
        "form_llm_provider": "web.form.llm_provider",
        "form_video_provider": "web.form.video_provider",
        "form_provider_config": "web.form.provider_config",
        "form_evaluator_mode": "web.form.evaluator_mode",
        "form_llm_model": "web.form.llm_model",
        "form_llm_base_url": "web.form.llm_base_url",
        "form_llm_api_key": "web.form.llm_api_key",
        "form_video_config": "web.form.video_config",
        "form_comfyui_base_url": "web.form.comfyui_base_url",
        "form_comfyui_workflows_dir": "web.form.comfyui_workflows_dir",
        "form_comfyui_workflow": "web.form.comfyui_workflow",
        "form_comfyui_search": "web.form.comfyui_search",
        "form_comfyui_searching": "web.form.comfyui_searching",
        "form_comfyui_search_failed": "web.form.comfyui_search_failed",
        "form_comfyui_search_found": "web.form.comfyui_search_found",
        "form_comfyui_search_empty": "web.form.comfyui_search_empty",
        "form_comfyui_width": "web.form.comfyui_width",
        "form_comfyui_height": "web.form.comfyui_height",
        "form_comfyui_length": "web.form.comfyui_length",
        "form_comfyui_fps": "web.form.comfyui_fps",
        "form_comfyui_max_shots": "web.form.comfyui_max_shots",
        "form_observer_provider": "web.form.observer_provider",
        "form_observer_config": "web.form.observer_config",
        "form_vlm_model": "web.form.vlm_model",
        "form_vlm_base_url": "web.form.vlm_base_url",
        "form_vlm_api_key": "web.form.vlm_api_key",
        "form_vlm_frame_sample_count": "web.form.vlm_frame_sample_count",
        "form_vlm_confidence_threshold": "web.form.vlm_confidence_threshold",
        "form_vlm_require_json": "web.form.vlm_require_json",
        "form_submit": "web.form.submit",
        "run_title": "web.run.title",
        "run_scene": "web.run.scene",
        "run_issues": "web.run.issues",
        "run_ready_title": "web.run.ready_title",
        "run_ready_body": "web.run.ready_body",
        "generation_title": "web.generation.title",
        "generation_provider": "web.generation.provider",
        "generation_video": "web.generation.video",
        "generation_prompt": "web.generation.prompt",
        "generation_prompt_json": "web.generation.prompt_json",
        "generation_workflow": "web.generation.workflow",
        "generation_iteration": "web.generation.iteration",
        "generation_artifacts": "web.generation.artifacts",
        "comfyui_workflows_title": "web.comfyui.workflows_title",
        "comfyui_workflow_available": "web.comfyui.workflow_available",
        "comfyui_workflow_unavailable": "web.comfyui.workflow_unavailable",
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


def _harness_inspector(state: ProjectState | None) -> dict[str, Any]:
    return build_harness_audit(state)


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    run_id: str | None = None,
    language: OutputLanguage = "zh",
) -> HTMLResponse:
    return _render_web_page(request, run_id=run_id, language=language, active_page="workflow")


@app.get("/config", response_class=HTMLResponse)
def config_page(
    request: Request,
    run_id: str | None = None,
    language: OutputLanguage = "zh",
) -> HTMLResponse:
    return _render_web_page(request, run_id=run_id, language=language, active_page="config")


def _render_web_page(
    request: Request,
    *,
    run_id: str | None,
    language: OutputLanguage,
    active_page: str,
    runtime_error: dict[str, Any] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    try:
        state = run_service.load_run(run_id) if run_id else None
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    active_language = state.language if state else language
    translator = get_translator()
    default_profile = provider_service.default_provider_profile()
    metadata = state.metadata if state else {}
    form_state = FormState(
        idea=state.user_idea if state else translator.t(active_language, "web.form.default_idea"),
        style=state.style if state else "cinematic",
        language=active_language,
        mode=str(state.metadata.get("run_mode", "design")) if state else "design",
        rubric_id=str(state.metadata.get("rubric_id", "baseline_v1")) if state else "baseline_v1",
        duration_seconds=state.duration_seconds if state else 24,
        max_iterations=int(state.metadata.get("max_iterations", 3)) if state else 3,
        provider_profile_id=str(metadata.get("provider_profile_id", default_profile.profile_id)),
        provider_profile_name=str(metadata.get("provider_profile_name", default_profile.name)),
        generator_provider_id=str(state.metadata.get("generator_provider_id", "mock"))
        if state
        else default_profile.generator_provider_id,
        llm_provider_id=str(metadata.get("llm_provider_id", default_profile.llm_provider_id)),
        llm_model=str(metadata.get("llm_model", default_profile.llm_model)),
        llm_base_url=str(metadata.get("llm_base_url", default_profile.llm_base_url)),
        llm_api_key="",
        evaluator_mode=str(metadata.get("evaluator_mode", default_profile.evaluator_mode)),
        comfyui_base_url=str(metadata.get("comfyui_base_url", default_profile.comfyui_base_url)),
        comfyui_workflows_dir=str(
            metadata.get(
                "comfyui_workflows_dir",
                default_profile.comfyui_workflows_dir or str(default_user_workflows_dir()),
            )
        ),
        comfyui_workflow_id=str(metadata.get("comfyui_workflow_id", default_profile.comfyui_workflow_id)),
        comfyui_width=int(metadata.get("comfyui_width", default_profile.comfyui_width)),
        comfyui_height=int(metadata.get("comfyui_height", default_profile.comfyui_height)),
        comfyui_length=int(metadata.get("comfyui_length", default_profile.comfyui_length)),
        comfyui_fps=float(metadata.get("comfyui_fps", default_profile.comfyui_fps)),
        comfyui_max_shots=int(metadata.get("comfyui_max_shots", default_profile.comfyui_max_shots)),
        observer_provider_id=str(
            metadata.get("observer_provider_id", default_profile.observer_provider_id)
        ),
        vlm_model=str(metadata.get("vlm_model", default_profile.vlm_model)),
        vlm_base_url=str(metadata.get("vlm_base_url", default_profile.vlm_base_url)),
        vlm_api_key="",
        vlm_frame_sample_count=int(
            metadata.get("vlm_frame_sample_count", default_profile.vlm_frame_sample_count)
        ),
        vlm_confidence_threshold=float(
            metadata.get("vlm_confidence_threshold", default_profile.vlm_confidence_threshold)
        ),
        vlm_require_json=bool(metadata.get("vlm_require_json", default_profile.vlm_require_json)),
    )
    workflow_status = provider_service.comfyui_workflow_status()
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
            "snapshots": run_service.version_snapshots(state),
            "llm_providers": provider_service.available_llm_providers(include_test=False),
            "generator_providers": provider_service.available_generator_providers(include_test=False),
            "observer_providers": provider_service.available_observer_providers(include_test=True),
            "comfyui_workflows": workflow_status["workflows"],
            "service_warnings": workflow_status["warnings"],
            "provider_profiles": provider_service.provider_profiles(include_test=False)
            or [default_profile.public_dict()],
            "run_history": run_service.list_run_history(),
            "generation_artifacts": artifact_service.generation_artifacts(state),
            "prompt_changes": run_service.prompt_change_cards(state),
            "run_progress": run_service.run_progress(state),
            "harness_inspector": _harness_inspector(state),
            "active_page": active_page,
            "runtime_error": runtime_error,
        },
        status_code=status_code,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/runs")
def create_run_form(
    request: Request,
    idea: str = Form(...),
    style: str = Form("cinematic"),
    language: OutputLanguage = Form("zh"),
    duration_seconds: int = Form(24),
    mode: str = Form("design"),
    rubric_id: str = Form("baseline_v1"),
    max_iterations: int = Form(3),
    provider_profile_id: str = Form("local-real"),
    provider_profile_name: str = Form("Local real generation"),
    generator_provider_id: str = Form("comfyui"),
    llm_provider_id: str = Form("ollama"),
    llm_model: str = Form("qwen2.5:7b"),
    llm_base_url: str = Form(""),
    llm_api_key: str = Form(""),
    evaluator_mode: str = Form("llm"),
    comfyui_base_url: str = Form(""),
    comfyui_workflows_dir: str = Form(""),
    comfyui_workflow_id: str = Form("wan2_2_i2v_empty_start"),
    comfyui_width: int = Form(320),
    comfyui_height: int = Form(320),
    comfyui_length: int = Form(9),
    comfyui_fps: float = Form(8.0),
    comfyui_max_shots: int = Form(0),
    observer_provider_id: str = Form("prompt-proxy"),
    vlm_model: str = Form(""),
    vlm_base_url: str = Form(""),
    vlm_api_key: str = Form(""),
    vlm_frame_sample_count: int = Form(4),
    vlm_confidence_threshold: float = Form(0.65),
    vlm_require_json: bool = Form(True),
) -> RedirectResponse:
    profile = provider_service.profile_from_form(
        provider_profile_id=provider_profile_id,
        provider_profile_name=provider_profile_name,
        llm_provider_id=llm_provider_id,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        evaluator_mode=evaluator_mode,
        generator_provider_id=generator_provider_id,
        comfyui_base_url=comfyui_base_url,
        comfyui_workflows_dir=comfyui_workflows_dir,
        comfyui_workflow_id=comfyui_workflow_id,
        comfyui_width=comfyui_width,
        comfyui_height=comfyui_height,
        comfyui_length=comfyui_length,
        comfyui_fps=comfyui_fps,
        comfyui_max_shots=comfyui_max_shots,
        observer_provider_id=observer_provider_id,
        vlm_model=vlm_model,
        vlm_base_url=vlm_base_url,
        vlm_api_key=vlm_api_key,
        vlm_frame_sample_count=vlm_frame_sample_count,
        vlm_confidence_threshold=vlm_confidence_threshold,
        vlm_require_json=vlm_require_json,
    )
    try:
        state = run_service.create_run(
            idea=idea,
            style=style,
            duration_seconds=duration_seconds,
            language=language,
            mode=mode,
            rubric_id=rubric_id,
            max_iterations=max_iterations,
            profile=profile,
            persist_profile=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        return _render_web_page(
            request,
            run_id=None,
            language=language,
            active_page="workflow",
            runtime_error=runtime_error_payload(exc),
            status_code=503,
        )
    return RedirectResponse(url=f"/?run_id={state.run_id}", status_code=303)


__all__ = ["app"]
