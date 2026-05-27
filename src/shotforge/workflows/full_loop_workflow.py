from __future__ import annotations

from shotforge.core.project_state import OutputLanguage, ProjectState
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.evaluation_workflow import run_evaluation_pipeline


def run_full_loop_pipeline(
    idea: str,
    style: str = "cinematic",
    duration_seconds: int = 24,
    language: OutputLanguage = "zh",
    rubric_id: str = "baseline_v1",
    generator_provider_id: str = "mock",
) -> ProjectState:
    state = run_design_pipeline(
        idea=idea,
        style=style,
        duration_seconds=duration_seconds,
        language=language,
    )
    return run_evaluation_pipeline(
        state,
        rubric_id=rubric_id,
        generator_provider_id=generator_provider_id,
        export=True,
    )
