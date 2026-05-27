from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HarnessContextSnapshot(BaseModel):
    agent_name: str
    source_count: int = 0
    char_count: int = 0
    source_types: list[str] = Field(default_factory=list)
    source_titles: list[str] = Field(default_factory=list)
    skill_count: int = 0
    skill_names: list[str] = Field(default_factory=list)
    mcp_tool_count: int = 0
    mcp_tool_names: list[str] = Field(default_factory=list)
    policy_id: str = ""
    execution_policy: dict[str, Any] = Field(default_factory=dict)
    sandbox_policy: dict[str, Any] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["HarnessContextSnapshot"]
