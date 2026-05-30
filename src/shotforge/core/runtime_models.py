from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

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


class AgentContractReport(BaseModel):
    agent_name: str
    contract_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    precondition_status: Literal["passed", "warning", "failed", "skipped"] = "skipped"
    postcondition_status: Literal["passed", "warning", "failed", "skipped"] = "skipped"
    blocking: bool = False
    verified_inputs: list[str] = Field(default_factory=list)
    verified_outputs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    missing_outputs: list[str] = Field(default_factory=list)
    precondition_issues: list[str] = Field(default_factory=list)
    postcondition_issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowDecisionRecord(BaseModel):
    agent_name: str
    timestamp: datetime = Field(default_factory=utc_now)
    decision: Literal["continue", "review", "refine", "repair", "block", "complete"]
    next_agent: str | None = None
    reason: str = ""
    severity: Literal["info", "warning", "critical"] = "info"
    required_actions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolOrchestrationRecord(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"tool_plan_{uuid4().hex[:12]}")
    requested_tool: str
    selected_tool: str = ""
    agent_name: str = ""
    purpose: str = ""
    expected_output: str = ""
    status: Literal[
        "planned",
        "completed",
        "failed",
        "denied",
        "fallback_completed",
        "fallback_failed",
    ] = "planned"
    authorization_decision: Literal["allowed", "denied"] = "allowed"
    authorization_reasons: list[str] = Field(default_factory=list)
    schema_status: Literal["passed", "warning", "failed", "skipped"] = "skipped"
    schema_issues: list[str] = Field(default_factory=list)
    fallback_tools: list[str] = Field(default_factory=list)
    attempted_tools: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AgentContractReport",
    "HarnessContextSnapshot",
    "StateTransitionRecord",
    "ToolCallRecord",
    "ToolOrchestrationRecord",
    "WorkflowDecisionRecord",
]
