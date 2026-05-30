from __future__ import annotations

from pydantic import BaseModel


class HarnessStrategyPolicy(BaseModel):
    policy_id: str = "default_harness_strategy_policy"
    enforce_preconditions: bool = True
    enforce_postconditions: bool = False
    record_contract_reports: bool = True
    record_workflow_decisions: bool = True
    route_on_contract_failure: bool = True


__all__ = ["HarnessStrategyPolicy"]
