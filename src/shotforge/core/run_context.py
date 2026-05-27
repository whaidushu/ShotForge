from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from shotforge.core.context_builder import ContextBundle


class RunContext(BaseModel):
    run_id: str
    project_id: str
    version: int
    agent_name: str
    language: str
    context_bundle: ContextBundle | None = None
    skill_names: list[str] = Field(default_factory=list)
    mcp_tool_names: list[str] = Field(default_factory=list)
    execution_policy: dict[str, Any] = Field(default_factory=dict)
    sandbox_policy: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["RunContext"]
