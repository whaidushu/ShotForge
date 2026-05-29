from __future__ import annotations

import json
from importlib.resources import files

from pydantic import BaseModel, Field


class SolutionPlaybook(BaseModel):
    playbook_id: str
    industries: list[str] = Field(default_factory=list)
    scenario_patterns: list[str] = Field(default_factory=list)
    value_levers: list[str] = Field(default_factory=list)
    required_integrations: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    evaluation_metrics: list[str] = Field(default_factory=list)


class SolutionPlaybookStore:
    def __init__(self, resource_name: str = "industry_solution_playbooks.json"):
        self.resource_name = resource_name

    def load(self) -> list[SolutionPlaybook]:
        payload = files("shotforge.knowledge").joinpath(self.resource_name).read_text(encoding="utf-8")
        return [SolutionPlaybook.model_validate(item) for item in json.loads(payload)]

    def find_for_industry(self, industry: str) -> SolutionPlaybook:
        playbooks = self.load()
        normalized = industry.lower()
        for playbook in playbooks:
            if any(item.lower() == normalized for item in playbook.industries):
                return playbook
        return playbooks[0]
