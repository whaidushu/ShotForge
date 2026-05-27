from __future__ import annotations

from dataclasses import dataclass

from shotforge.agents.correction import CorrectionAgentRegistry
from shotforge.core.project_state import CorrectionPlan


@dataclass(frozen=True)
class CorrectionRoute:
    plan_id: str
    correction_type: str
    selected_agent: str
    status: str
    reason: str = ""


class CorrectionRouter:
    def route(self, plan: CorrectionPlan, registry: CorrectionAgentRegistry) -> CorrectionRoute:
        correction_type = str(plan.metadata.get("correction_type", "")).strip()
        if not correction_type and plan.selected_agent.endswith("_correction_agent"):
            correction_type = plan.selected_agent.removesuffix("_correction_agent")
        if not correction_type:
            return CorrectionRoute(
                plan_id=plan.plan_id,
                correction_type="",
                selected_agent=plan.selected_agent,
                status="skipped",
                reason="missing_correction_type",
            )
        agent = registry.get(correction_type)
        if agent is None:
            return CorrectionRoute(
                plan_id=plan.plan_id,
                correction_type=correction_type,
                selected_agent=f"{correction_type}_correction_agent",
                status="skipped",
                reason="no_registered_agent",
            )
        return CorrectionRoute(
            plan_id=plan.plan_id,
            correction_type=correction_type,
            selected_agent=agent.agent_name,
            status="routed",
        )
