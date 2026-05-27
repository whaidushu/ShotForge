from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from shotforge.core.project_state import GeneratedResult, ProjectState
from shotforge.core.schemas.evaluation import EvaluationRubric


class EvaluationSignal(BaseModel):
    signal_id: str
    source: str
    dimension_id: str
    score: float = Field(ge=0, le=1)
    shot_id: str | None = None
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)
    metadata: dict = Field(default_factory=dict)


class EvaluatorContext(BaseModel):
    state: ProjectState
    generated_result: GeneratedResult
    rubric: EvaluationRubric

    model_config = {"arbitrary_types_allowed": True}


class EvaluatorProvider(Protocol):
    evaluator_id: str

    def evaluate(self, context: EvaluatorContext) -> list[EvaluationSignal]:
        """Return raw evaluation signals for one or more dimensions."""
