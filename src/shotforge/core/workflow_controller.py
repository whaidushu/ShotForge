from __future__ import annotations

from pydantic import BaseModel, Field

from shotforge.core.project_state import ProjectState
from shotforge.core.runtime_models import AgentContractReport, WorkflowDecisionRecord


class WorkflowRoutingPolicy(BaseModel):
    policy_id: str = "default_workflow_routing_policy"
    route_map: dict[str, str | None] = Field(
        default_factory=lambda: {
            "intent_agent": "storyboard_agent",
            "storyboard_agent": "motion_agent",
            "motion_agent": "audio_cue_agent",
            "audio_cue_agent": "prompt_adapter_agent",
            "prompt_adapter_agent": "solution_architect_agent",
            "solution_architect_agent": "delivery_readiness_agent",
            "delivery_readiness_agent": "export_agent",
            "export_agent": None,
        }
    )
    review_on_readiness_warning: bool = True
    refine_on_contract_failure: bool = True


class WorkflowController:
    def __init__(self, policy: WorkflowRoutingPolicy | None = None):
        self.policy = policy or WorkflowRoutingPolicy()

    def decide(
        self,
        state: ProjectState,
        agent_name: str,
        contract_report: AgentContractReport | None = None,
    ) -> WorkflowDecisionRecord:
        next_agent = self.policy.route_map.get(agent_name)
        if contract_report and contract_report.precondition_status == "failed":
            return WorkflowDecisionRecord(
                agent_name=agent_name,
                decision="block",
                next_agent=None,
                reason="Agent preconditions failed.",
                severity="critical",
                required_actions=contract_report.precondition_issues,
                metadata=self._metadata(contract_report),
            )
        if (
            contract_report
            and contract_report.postcondition_status == "failed"
            and self.policy.refine_on_contract_failure
        ):
            return WorkflowDecisionRecord(
                agent_name=agent_name,
                decision="repair",
                next_agent=self._repair_target(agent_name),
                reason="Agent output contract failed.",
                severity="critical",
                required_actions=contract_report.postcondition_issues,
                metadata=self._metadata(contract_report),
            )
        if agent_name == "delivery_readiness_agent" and state.delivery_readiness:
            if (
                self.policy.review_on_readiness_warning
                and state.delivery_readiness.overall_status in {"warning", "failed"}
            ):
                return WorkflowDecisionRecord(
                    agent_name=agent_name,
                    decision="review",
                    next_agent="review_refine",
                    reason=f"Delivery readiness is {state.delivery_readiness.overall_status}.",
                    severity=(
                        "critical"
                        if state.delivery_readiness.overall_status == "failed"
                        else "warning"
                    ),
                    required_actions=state.delivery_readiness.next_actions,
                    metadata=self._metadata(contract_report),
                )
        if agent_name == "export_agent":
            return WorkflowDecisionRecord(
                agent_name=agent_name,
                decision="complete",
                next_agent=None,
                reason="Export package completed.",
                metadata=self._metadata(contract_report),
            )
        return WorkflowDecisionRecord(
            agent_name=agent_name,
            decision="continue",
            next_agent=next_agent,
            reason="Static route policy selected the next agent.",
            metadata=self._metadata(contract_report),
        )

    def _repair_target(self, agent_name: str) -> str:
        return {
            "storyboard_agent": "storyboard_agent",
            "motion_agent": "motion_agent",
            "audio_cue_agent": "audio_cue_agent",
            "prompt_adapter_agent": "prompt_adapter_agent",
            "solution_architect_agent": "solution_architect_agent",
            "delivery_readiness_agent": "delivery_readiness_agent",
            "export_agent": "export_agent",
        }.get(agent_name, "review_refine")

    def _metadata(self, contract_report: AgentContractReport | None) -> dict[str, object]:
        return {
            "routing_policy_id": self.policy.policy_id,
            "contract_id": contract_report.contract_id if contract_report else "",
            "contract_precondition_status": (
                contract_report.precondition_status if contract_report else "skipped"
            ),
            "contract_postcondition_status": (
                contract_report.postcondition_status if contract_report else "skipped"
            ),
        }


__all__ = ["WorkflowController", "WorkflowRoutingPolicy"]
