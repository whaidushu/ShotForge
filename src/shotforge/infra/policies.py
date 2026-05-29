from __future__ import annotations

from pydantic import BaseModel


class ExecutionPolicy(BaseModel):
    policy_id: str = "default_agent_harness_policy"
    max_context_chars: int = 6000
    allow_network_tools: bool = False
    allow_filesystem_tools: bool = True
    max_tool_calls_per_agent: int = 8


__all__ = ["ExecutionPolicy"]
