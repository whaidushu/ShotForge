from __future__ import annotations

from shotforge.agents.evaluation import SuggestionAgent
from shotforge.core.project_state import CorrectionPlan, EvaluationReport, ProjectState


def run_redesign_planning(
    state: ProjectState,
    report: EvaluationReport | None = None,
) -> list[CorrectionPlan]:
    return SuggestionAgent().plan(state, report=report)
