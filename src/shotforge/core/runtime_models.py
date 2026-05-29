from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ToolCallRecord(BaseModel):
    tool_name: str
    status: Literal["started", "completed", "failed"] = "completed"
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: float | None = None
    input_preview: str = ""
    output_preview: str = ""
    error: str | None = None
    permission_scope: str = "local"
    metadata: dict[str, Any] = Field(default_factory=dict)


class HarnessContextSnapshot(BaseModel):
    agent_name: str
    timestamp: datetime = Field(default_factory=utc_now)
    source_count: int = 0
    char_count: int = 0
    source_types: list[str] = Field(default_factory=list)
    source_titles: list[str] = Field(default_factory=list)
    skill_count: int = 0
    skill_names: list[str] = Field(default_factory=list)
    mcp_tool_count: int = 0
    mcp_tool_names: list[str] = Field(default_factory=list)
    execution_policy: dict[str, Any] = Field(default_factory=dict)
    sandbox_policy: dict[str, Any] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StateTransitionRecord(BaseModel):
    agent_name: str
    timestamp: datetime = Field(default_factory=utc_now)
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    changed_fields: list[str] = Field(default_factory=list)
    invariant_status: Literal["passed", "warning", "failed"] = "passed"
    invariant_issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["HarnessContextSnapshot", "StateTransitionRecord", "ToolCallRecord"]
