from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationLayerConfig(BaseModel):
    id: str
    index: int
    labels: dict[str, str]
    objective: str = ""
    convergence_policy: str = "fix-before-next-layer"
    metadata: dict = Field(default_factory=dict)

    def label(self, language: str) -> str:
        return self.labels.get(language) or self.labels.get("en") or self.id


class EvaluationIssueRule(BaseModel):
    threshold: float = 0.72
    severity_bands: dict[str, float] = Field(
        default_factory=lambda: {"critical": 0.35, "high": 0.5, "medium": 0.72}
    )
    correction_type: str = "prompt"
    description_template: str
    cause_template: str
    description_templates: dict[str, str] = Field(default_factory=dict)
    cause_templates: dict[str, str] = Field(default_factory=dict)

    def description(self, language: str) -> str:
        return (
            self.description_templates.get(language)
            or self.description_templates.get("en")
            or self.description_template
        )

    def cause(self, language: str) -> str:
        return self.cause_templates.get(language) or self.cause_templates.get("en") or self.cause_template


class EvaluationDimensionConfig(BaseModel):
    id: str
    labels: dict[str, str]
    weight: float = 1.0
    target: str = ""
    signal_key: str | None = None
    layer_id: str = "creative_quality"
    layer_index: int = 99
    prompt_fields: list[str] = Field(default_factory=list)
    hard_target: bool = False
    issue_rule: EvaluationIssueRule
    metadata: dict = Field(default_factory=dict)

    def label(self, language: str) -> str:
        return self.labels.get(language) or self.labels.get("en") or self.id


class EvaluationRubric(BaseModel):
    id: str
    version: str = "1.0"
    labels: dict[str, str] = Field(default_factory=dict)
    layers: list[EvaluationLayerConfig] = Field(default_factory=list)
    dimensions: list[EvaluationDimensionConfig]
    metadata: dict = Field(default_factory=dict)

    def label(self, language: str) -> str:
        return self.labels.get(language) or self.labels.get("en") or self.id

    def layer(self, layer_id: str) -> EvaluationLayerConfig | None:
        return next((layer for layer in self.layers if layer.id == layer_id), None)
