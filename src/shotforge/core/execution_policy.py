from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]


class ExecutionPolicy(BaseModel):
    policy_id: str = "default_agent_harness_policy"
    allow_skill_calls: bool = True
    allow_mcp_calls: bool = False
    allow_network: bool = False
    allow_file_read: bool = True
    allow_file_write: bool = True
    max_runtime_ms: int = 30000
    max_context_chars: int = 8000
    denied_skill_scopes: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def allows_scope(self, scope: str) -> bool:
        return scope not in self.denied_skill_scopes


__all__ = ["ExecutionPolicy", "RiskLevel"]
