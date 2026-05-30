from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from shotforge.core.project_state import ProjectState
from shotforge.core.runtime_models import AgentContractReport


RequirementKind = Literal[
    "exists",
    "non_empty",
    "all_shots_have_motion",
    "audio_matches_shots",
    "prompts_match_shots",
    "solution_ready",
    "delivery_ready",
    "exports_present",
]


class ContractRequirement(BaseModel):
    path: str
    kind: RequirementKind = "exists"
    required: bool = True
    description: str = ""


class AgentContract(BaseModel):
    agent_name: str
    contract_id: str
    required_inputs: list[ContractRequirement] = Field(default_factory=list)
    required_outputs: list[ContractRequirement] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    def evaluate_preconditions(self, state: ProjectState) -> AgentContractReport:
        passed, failed = self._evaluate_requirements(state, self.required_inputs)
        return AgentContractReport(
            agent_name=self.agent_name,
            contract_id=self.contract_id,
            precondition_status="passed" if not failed else "failed",
            postcondition_status="skipped",
            blocking=bool(failed),
            verified_inputs=passed,
            missing_inputs=failed,
            precondition_issues=[f"missing_or_invalid_input:{item}" for item in failed],
            metadata={"phase": "precondition", **self.metadata},
        )

    def evaluate(
        self,
        state: ProjectState,
        precondition_report: AgentContractReport,
    ) -> AgentContractReport:
        passed, failed = self._evaluate_requirements(state, self.required_outputs)
        return AgentContractReport(
            agent_name=self.agent_name,
            contract_id=self.contract_id,
            precondition_status=precondition_report.precondition_status,
            postcondition_status="passed" if not failed else "failed",
            blocking=bool(precondition_report.blocking),
            verified_inputs=precondition_report.verified_inputs,
            verified_outputs=passed,
            missing_inputs=precondition_report.missing_inputs,
            missing_outputs=failed,
            precondition_issues=precondition_report.precondition_issues,
            postcondition_issues=[f"missing_or_invalid_output:{item}" for item in failed],
            metadata={"phase": "postcondition", **self.metadata},
        )

    def _evaluate_requirements(
        self,
        state: ProjectState,
        requirements: list[ContractRequirement],
    ) -> tuple[list[str], list[str]]:
        passed: list[str] = []
        failed: list[str] = []
        for requirement in requirements:
            ok = self._requirement_passes(state, requirement)
            target = passed if ok else failed
            target.append(requirement.path)
        return passed, failed

    def _requirement_passes(self, state: ProjectState, requirement: ContractRequirement) -> bool:
        if not requirement.required:
            return True
        if requirement.kind == "all_shots_have_motion":
            return bool(state.shots) and all(shot.motion is not None for shot in state.shots)
        if requirement.kind == "audio_matches_shots":
            return bool(state.shots) and len(state.audio_cues) == len(state.shots)
        if requirement.kind == "prompts_match_shots":
            return bool(state.shots) and len(state.prompt_package.prompts) == len(state.shots)
        if requirement.kind == "solution_ready":
            return state.solution_architecture is not None
        if requirement.kind == "delivery_ready":
            return state.delivery_readiness is not None
        if requirement.kind == "exports_present":
            return bool(state.exports)

        value = _read_path(state, requirement.path)
        if requirement.kind == "exists":
            return value is not None
        if requirement.kind == "non_empty":
            return bool(value)
        return False


class AgentContractRegistry:
    def __init__(self, contracts: list[AgentContract] | None = None):
        self._contracts: dict[str, AgentContract] = {}
        for contract in contracts or []:
            self.register(contract)

    def register(self, contract: AgentContract) -> None:
        if contract.agent_name in self._contracts:
            raise ValueError(f"Agent contract already registered: {contract.agent_name}")
        self._contracts[contract.agent_name] = contract

    def get(self, agent_name: str) -> AgentContract | None:
        return self._contracts.get(agent_name)

    def list(self) -> list[AgentContract]:
        return [self._contracts[name] for name in sorted(self._contracts)]


def build_default_agent_contract_registry() -> AgentContractRegistry:
    def req(path: str, kind: RequirementKind = "exists") -> ContractRequirement:
        return ContractRequirement(path=path, kind=kind)

    return AgentContractRegistry(
        [
            AgentContract(
                agent_name="intent_agent",
                contract_id="intent_contract_v1",
                required_inputs=[req("user_idea", "non_empty"), req("style", "non_empty")],
                required_outputs=[req("creative_intent"), req("characters", "non_empty")],
            ),
            AgentContract(
                agent_name="storyboard_agent",
                contract_id="storyboard_contract_v1",
                required_inputs=[req("creative_intent")],
                required_outputs=[req("scenes", "non_empty"), req("shots", "non_empty")],
            ),
            AgentContract(
                agent_name="motion_agent",
                contract_id="motion_contract_v1",
                required_inputs=[req("shots", "non_empty")],
                required_outputs=[req("shots.motion", "all_shots_have_motion")],
            ),
            AgentContract(
                agent_name="audio_cue_agent",
                contract_id="audio_contract_v1",
                required_inputs=[req("shots.motion", "all_shots_have_motion")],
                required_outputs=[req("audio_cues", "audio_matches_shots")],
            ),
            AgentContract(
                agent_name="prompt_adapter_agent",
                contract_id="prompt_adapter_contract_v1",
                required_inputs=[req("audio_cues", "audio_matches_shots")],
                required_outputs=[req("prompt_package.prompts", "prompts_match_shots")],
            ),
            AgentContract(
                agent_name="solution_architect_agent",
                contract_id="solution_architect_contract_v1",
                required_inputs=[req("prompt_package.prompts", "prompts_match_shots")],
                required_outputs=[req("solution_architecture", "solution_ready")],
            ),
            AgentContract(
                agent_name="delivery_readiness_agent",
                contract_id="delivery_readiness_contract_v1",
                required_inputs=[req("solution_architecture", "solution_ready")],
                required_outputs=[req("delivery_readiness", "delivery_ready")],
            ),
            AgentContract(
                agent_name="export_agent",
                contract_id="export_contract_v1",
                required_inputs=[req("delivery_readiness", "delivery_ready")],
                required_outputs=[req("exports", "exports_present")],
            ),
        ]
    )


def _read_path(state: ProjectState, path: str):
    value = state
    for part in path.split("."):
        if value is None:
            return None
        value = getattr(value, part, None)
    return value


__all__ = [
    "AgentContract",
    "AgentContractRegistry",
    "ContractRequirement",
    "build_default_agent_contract_registry",
]
