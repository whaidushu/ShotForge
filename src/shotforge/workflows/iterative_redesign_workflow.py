from __future__ import annotations

from shotforge.core.convergence_engine import ConvergenceEngine
from shotforge.core.project_state import ProjectState
from shotforge.core.trace_log import TraceLog
from shotforge.core.version_manager import VersionManager
from shotforge.workflows.redesign_workflow import run_redesign


def run_iterative_redesign(
    state: ProjectState,
    max_iterations: int = 3,
    min_delta: float = 0.005,
    generator_provider_id: str | None = None,
) -> ProjectState:
    engine = ConvergenceEngine(max_iterations=max_iterations, min_delta=min_delta)
    version_manager = VersionManager()
    current_state = state
    with TraceLog(current_state).span(
        "iterative_redesign_workflow",
        max_iterations=max_iterations,
        min_delta=min_delta,
    ):
        version_manager.save_snapshot(current_state, label="convergence_start")
        for iteration_index in range(1, max_iterations + 1):
            current_state = run_redesign(
                current_state,
                report=current_state.evaluation_reports[-1],
                generator_provider_id=generator_provider_id,
            )
            stop_condition = engine.evaluate_stop_condition(current_state, iteration_index)
            engine.record_step(current_state, stop_condition)
            version_manager.save_snapshot(current_state, label=f"redesign_iter_{iteration_index}")
            if stop_condition.should_stop:
                break
    return current_state
