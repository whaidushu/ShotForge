from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentSpec(BaseModel):
    agent_name: str
    role: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    extension_points: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentCatalog:
    def __init__(self, specs: list[AgentSpec] | None = None):
        self._specs: dict[str, AgentSpec] = {}
        for spec in specs or []:
            self.register(spec)

    def register(self, spec: AgentSpec) -> None:
        if spec.agent_name in self._specs:
            raise ValueError(f"Agent spec already registered: {spec.agent_name}")
        self._specs[spec.agent_name] = spec

    def get(self, agent_name: str) -> AgentSpec:
        try:
            return self._specs[agent_name]
        except KeyError as exc:
            raise KeyError(f"Agent spec not registered: {agent_name}") from exc

    def list(self) -> list[AgentSpec]:
        return [self._specs[name] for name in sorted(self._specs)]

    def dependency_edges(self) -> list[dict[str, str]]:
        edges: list[dict[str, str]] = []
        for spec in self.list():
            for dependency in spec.dependencies:
                edges.append({"from": dependency, "to": spec.agent_name})
        return edges
