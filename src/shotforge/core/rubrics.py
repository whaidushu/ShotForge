from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from shotforge.core.schemas.evaluation import EvaluationRubric


class RubricRegistry:
    def __init__(self, path: Path | None = None):
        self.path = path

    def load(self, rubric_id: str = "baseline_v1") -> EvaluationRubric:
        data = self._load_json()
        rubrics = [EvaluationRubric.model_validate(item) for item in data["rubrics"]]
        for rubric in rubrics:
            if rubric.id == rubric_id:
                return rubric
        available = ", ".join(rubric.id for rubric in rubrics)
        raise KeyError(f"Rubric not found: {rubric_id}. Available: {available}")

    def _load_json(self) -> dict:
        if self.path:
            return json.loads(self.path.read_text(encoding="utf-8"))
        resource = files("shotforge.knowledge").joinpath("evaluation_rubrics.json")
        return json.loads(resource.read_text(encoding="utf-8"))
