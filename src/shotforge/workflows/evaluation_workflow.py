from __future__ import annotations

from pathlib import Path

from shotforge.agents.evaluation import EvaluationAgent, VerificationAgent
from shotforge.core.project_state import (
    EvaluationReport,
    GeneratedResult,
    ProjectState,
    VerificationReport,
)
from shotforge.exporters import ExportManager
from shotforge.generators import build_default_generator_registry
from shotforge.observation import VideoObservationService


def run_generation(state: ProjectState, provider_id: str = "mock") -> GeneratedResult:
    provider = build_default_generator_registry().get(provider_id)
    state.metadata["generator_provider_id"] = provider.provider_id
    state.metadata["generator_display_name"] = provider.display_name
    state.metadata["generator_supports_real_generation"] = provider.supports_real_generation()
    state.metadata["generator_cost_estimate"] = provider.estimate_cost(state).model_dump(mode="json")
    state.metadata["generator_capabilities"] = provider.capabilities().model_dump(mode="json")
    return provider.generate(state)


def run_mock_generation(state: ProjectState) -> GeneratedResult:
    return run_generation(state, provider_id="mock")


def run_evaluation(
    state: ProjectState,
    generated_result: GeneratedResult | None = None,
    rubric_id: str = "baseline_v1",
) -> EvaluationReport:
    return EvaluationAgent().evaluate(state, generated_result=generated_result, rubric_id=rubric_id)


def run_verification(
    state: ProjectState,
    generated_result: GeneratedResult,
) -> VerificationReport:
    return VerificationAgent().verify(state, generated_result)


def run_evaluation_pipeline(
    state: ProjectState,
    rubric_id: str = "baseline_v1",
    generator_provider_id: str = "mock",
    export: bool = True,
) -> ProjectState:
    generated_result = run_generation(state, provider_id=generator_provider_id)
    observe_generation(state, generated_result)
    run_verification(state, generated_result)
    run_evaluation(state, generated_result=generated_result, rubric_id=rubric_id)
    if export:
        ExportManager().export_all(state)
    return state


def load_project_state(package_json: Path) -> ProjectState:
    return ProjectState.model_validate_json(package_json.read_text(encoding="utf-8"))


def observe_generation(
    state: ProjectState,
    generated_result: GeneratedResult,
) -> GeneratedResult:
    return VideoObservationService().observe_result(state, generated_result)
