from __future__ import annotations

from collections.abc import Callable

from shotforge.core.agent_contract import (
    AgentContractRegistry,
    build_default_agent_contract_registry,
)
from shotforge.core.agent_catalog import AgentCatalog
from shotforge.core.context_builder import ContextBuilder
from shotforge.core.harness_policy import HarnessStrategyPolicy
from shotforge.core.project_state import ProjectState
from shotforge.core.runtime_models import (
    AgentContractReport,
    HarnessContextSnapshot,
    SandboxPolicyRecord,
    StateTransitionRecord,
    ToolCallRecord,
)
from shotforge.core.trace_log import TraceLog
from shotforge.core.workflow_controller import WorkflowController
from shotforge.infra.mcp import LocalMCPAdapter, build_default_mcp_adapter
from shotforge.infra.memory import LocalMemoryStore, MemoryManager
from shotforge.infra.policies import ExecutionPolicy
from shotforge.infra.sandbox import SandboxPolicy
from shotforge.skills import SkillRegistry


class AgentHarnessRuntime:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        registry: SkillRegistry | None = None,
        execution_policy: ExecutionPolicy | None = None,
        sandbox_policy: SandboxPolicy | None = None,
        mcp_adapter: LocalMCPAdapter | None = None,
        memory_store: LocalMemoryStore | None = None,
        memory_manager: MemoryManager | None = None,
        agent_catalog: AgentCatalog | None = None,
        contract_registry: AgentContractRegistry | None = None,
        workflow_controller: WorkflowController | None = None,
        harness_policy: HarnessStrategyPolicy | None = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.registry = registry or SkillRegistry()
        self.execution_policy = execution_policy or ExecutionPolicy()
        self.sandbox_policy = sandbox_policy or SandboxPolicy()
        self.mcp_adapter = mcp_adapter or build_default_mcp_adapter()
        self.memory_store = memory_store or LocalMemoryStore()
        self.memory_manager = memory_manager or MemoryManager(self.memory_store)
        self.agent_catalog = agent_catalog
        self.contract_registry = contract_registry or build_default_agent_contract_registry()
        self.workflow_controller = workflow_controller or WorkflowController()
        self.harness_policy = harness_policy or HarnessStrategyPolicy()

    def run_agent(
        self,
        state: ProjectState,
        agent_name: str,
        handler: Callable[[ProjectState], ProjectState],
        tags: list[str] | None = None,
    ) -> ProjectState:
        with TraceLog(state).span("agent_harness_runtime", agent_name=agent_name):
            precondition_report = self._evaluate_preconditions(state, agent_name)
            before_mcp_access_count = len(self.mcp_adapter.access_records())
            self._record_context(state, agent_name, tags=tags)
            self._record_mcp_access(state, before_mcp_access_count)
            self._record_sandbox_policy_snapshot(state, agent_name)
            before_record_count = len(self.registry.records())
            before_orchestration_count = len(self.registry.orchestration_records())
            before_summary = self._state_summary(state)
            result = handler(state)
            self._record_state_transition(result, agent_name, before_summary)
            contract_report = self._record_contract_report(
                result,
                agent_name,
                precondition_report,
            )
            self._record_workflow_decision(result, agent_name, contract_report)
            self._enforce_tool_budget(result, agent_name, before_record_count)
            self._record_tool_calls(result, before_record_count)
            self._record_tool_orchestration(result, before_orchestration_count)
            self._maybe_promote_memory(result, agent_name)
            return result

    def _evaluate_preconditions(
        self,
        state: ProjectState,
        agent_name: str,
    ) -> AgentContractReport | None:
        contract = self.contract_registry.get(agent_name)
        if contract is None:
            return None
        report = contract.evaluate_preconditions(state)
        if report.precondition_status == "failed" and self.harness_policy.enforce_preconditions:
            state.agent_contract_reports.append(report)
            state.workflow_decisions.append(
                self.workflow_controller.decide(state, agent_name, report)
            )
            state.touch()
            raise PermissionError(
                f"Agent preconditions failed for {agent_name}: "
                f"{', '.join(report.missing_inputs)}"
            )
        return report

    def _record_contract_report(
        self,
        state: ProjectState,
        agent_name: str,
        precondition_report: AgentContractReport | None,
    ) -> AgentContractReport | None:
        contract = self.contract_registry.get(agent_name)
        if contract is None or precondition_report is None:
            return None
        report = contract.evaluate(state, precondition_report)
        if self.harness_policy.record_contract_reports:
            state.agent_contract_reports.append(report)
            state.touch()
        if report.postcondition_status == "failed" and self.harness_policy.enforce_postconditions:
            raise PermissionError(
                f"Agent postconditions failed for {agent_name}: "
                f"{', '.join(report.missing_outputs)}"
            )
        return report

    def _record_workflow_decision(
        self,
        state: ProjectState,
        agent_name: str,
        contract_report: AgentContractReport | None,
    ) -> None:
        if not self.harness_policy.record_workflow_decisions:
            return
        state.workflow_decisions.append(
            self.workflow_controller.decide(state, agent_name, contract_report)
        )
        state.touch()

    def _record_context(
        self,
        state: ProjectState,
        agent_name: str,
        tags: list[str] | None = None,
    ) -> None:
        context = self.context_builder.build(
            state,
            agent_name,
            tags=tags,
            max_chars=self.execution_policy.max_context_chars,
        )
        memory_hits, memory_selection = self.memory_manager.select(
            state,
            agent_name,
            tags=tags,
            query=state.user_idea,
        )
        state.memory_selection_records.append(memory_selection)
        for record in memory_hits:
            if record.memory_id not in state.memory_refs:
                state.memory_refs.append(record.memory_id)

        state.harness_contexts.append(
            HarnessContextSnapshot(
                agent_name=agent_name,
                source_count=len([source for source in context.sources if source.included])
                + len(memory_hits),
                char_count=context.char_count,
                source_types=[
                    *[source.source_type for source in context.sources if source.included],
                    *["memory" for _ in memory_hits],
                ],
                source_titles=[
                    *[source.title for source in context.sources if source.included],
                    *[item.kind for item in memory_hits],
                ],
                skill_count=len(self.registry.names()),
                skill_names=self.registry.names(),
                mcp_tool_count=len(self.mcp_adapter.list_tools()),
                mcp_tool_names=[tool.name for tool in self.mcp_adapter.list_tools()],
                execution_policy=self.execution_policy.model_dump(mode="json"),
                sandbox_policy=self.sandbox_policy.model_dump(mode="json"),
                memory={
                    "provider": self.memory_store.__class__.__name__,
                    "hits": len(memory_hits),
                    "memory_ids": [record.memory_id for record in memory_hits],
                },
                metadata={
                    "context_digest": context.digest,
                    "context_max_chars": context.max_chars,
                    "context_truncated": context.truncated,
                    "agent_spec": self._agent_spec_metadata(agent_name),
                    "source_priorities": {
                        source.source_id: source.priority for source in context.sources
                    },
                    "excluded_sources": [
                        source.source_id for source in context.sources if not source.included
                    ],
                    "redacted_sources": [
                        source.source_id for source in context.sources if source.redacted
                    ],
                    "memory_selection_id": memory_selection.selection_id,
                    "memory_selection_reasons": memory_selection.reasons,
                },
            )
        )
        state.touch()

    def _record_tool_calls(self, state: ProjectState, before_record_count: int) -> None:
        records = self.registry.records()[before_record_count:]
        state.tool_call_records.extend(records)
        state.touch()

    def _record_mcp_access(self, state: ProjectState, before_access_count: int) -> None:
        records = self.mcp_adapter.access_records()[before_access_count:]
        state.mcp_access_records.extend(records)
        state.touch()

    def _record_sandbox_policy_snapshot(self, state: ProjectState, agent_name: str) -> None:
        state.sandbox_policy_records.append(
            SandboxPolicyRecord(
                command=[],
                decision="allowed",
                reason="policy_snapshot",
                profile_id=self.sandbox_policy.execution_profile.profile_id,
                working_dir=str(self.sandbox_policy.working_dir),
                allow_network=self.sandbox_policy.allow_network,
                allow_file_write=self.sandbox_policy.allow_file_write,
                allowed_env_keys=self.sandbox_policy.allowed_env_keys,
                metadata={
                    "agent_name": agent_name,
                    "sandbox_id": self.sandbox_policy.sandbox_id,
                    "dry_run": self.sandbox_policy.dry_run,
                    "require_workspace_boundary": self.sandbox_policy.require_workspace_boundary,
                },
            )
        )
        state.touch()

    def _record_tool_orchestration(
        self,
        state: ProjectState,
        before_orchestration_count: int,
    ) -> None:
        records = self.registry.orchestration_records()[before_orchestration_count:]
        state.tool_orchestration_records.extend(records)
        state.touch()

    def _enforce_tool_budget(
        self,
        state: ProjectState,
        agent_name: str,
        before_record_count: int,
    ) -> None:
        records = self.registry.records()[before_record_count:]
        max_calls = self.execution_policy.max_tool_calls_per_agent
        if len(records) <= max_calls:
            return
        violation = ToolCallRecord(
            tool_name="agent_harness.tool_budget",
            status="failed",
            error=(
                f"Agent {agent_name} exceeded tool call budget: "
                f"{len(records)} > {max_calls}"
            ),
            permission_scope="runtime_policy",
            metadata={
                "agent_name": agent_name,
                "tool_call_count": len(records),
                "max_tool_calls_per_agent": max_calls,
                "policy_id": self.execution_policy.policy_id,
            },
        )
        state.tool_call_records.extend(records)
        state.tool_call_records.append(violation)
        state.touch()
        raise PermissionError(violation.error)

    def _record_state_transition(
        self,
        state: ProjectState,
        agent_name: str,
        before_summary: dict[str, int | str],
    ) -> None:
        after_summary = self._state_summary(state)
        changed_fields = [
            key
            for key, before_value in before_summary.items()
            if after_summary.get(key) != before_value
        ]
        invariant_issues = self._invariant_issues(state, agent_name)
        state.state_transitions.append(
            StateTransitionRecord(
                agent_name=agent_name,
                before=before_summary,
                after=after_summary,
                changed_fields=changed_fields,
                invariant_status="warning" if invariant_issues else "passed",
                invariant_issues=invariant_issues,
                metadata={
                    "changed_count": len(changed_fields),
                    "project_id": state.project_id,
                    "run_id": state.run_id,
                },
            )
        )
        state.touch()

    def _state_summary(self, state: ProjectState) -> dict[str, int | str]:
        return {
            "version": state.version,
            "creative_intent": 1 if state.creative_intent else 0,
            "characters": len(state.characters),
            "scenes": len(state.scenes),
            "shots": len(state.shots),
            "audio_cues": len(state.audio_cues),
            "prompts": len(state.prompt_package.prompts),
            "solution_architecture": 1 if state.solution_architecture else 0,
            "delivery_readiness": 1 if state.delivery_readiness else 0,
            "evaluations": len(state.evaluation_reports),
            "exports": len(state.exports),
            "trace_logs": len(state.trace_logs),
            "tool_orchestration_records": len(state.tool_orchestration_records),
            "agent_contract_reports": len(state.agent_contract_reports),
            "workflow_decisions": len(state.workflow_decisions),
            "memory_selection_records": len(state.memory_selection_records),
            "sandbox_policy_records": len(state.sandbox_policy_records),
            "mcp_access_records": len(state.mcp_access_records),
        }

    def _invariant_issues(self, state: ProjectState, agent_name: str) -> list[str]:
        issues: list[str] = []
        if agent_name in {"storyboard_agent", "motion_agent", "audio_cue_agent"} and not state.shots:
            issues.append("shots_missing_after_story_phase")
        if agent_name in {"audio_cue_agent", "prompt_adapter_agent"} and state.shots:
            if state.audio_cues and len(state.audio_cues) != len(state.shots):
                issues.append("audio_cue_count_does_not_match_shots")
        if agent_name in {"prompt_adapter_agent", "solution_architect_agent", "export_agent"}:
            prompt_count = len(state.prompt_package.prompts)
            if state.shots and prompt_count != len(state.shots):
                issues.append("prompt_count_does_not_match_shots")
        if agent_name == "solution_architect_agent" and state.solution_architecture is None:
            issues.append("solution_architecture_missing")
        if agent_name == "delivery_readiness_agent" and state.delivery_readiness is None:
            issues.append("delivery_readiness_missing")
        return issues

    def _agent_spec_metadata(self, agent_name: str) -> dict:
        if self.agent_catalog is None:
            return {}
        try:
            spec = self.agent_catalog.get(agent_name)
        except KeyError:
            return {}
        return {
            "role": spec.role,
            "inputs": spec.inputs,
            "outputs": spec.outputs,
            "dependencies": spec.dependencies,
            "extension_points": spec.extension_points,
        }

    def _maybe_promote_memory(self, state: ProjectState, agent_name: str) -> None:
        record, decision = self.memory_manager.promote_run(state, agent_name)
        state.memory_selection_records.append(decision)
        if record is None:
            state.touch()
            return
        if record.memory_id not in state.memory_refs:
            state.memory_refs.append(record.memory_id)
        state.metadata["memory_promoted_run_id"] = state.run_id
        state.touch()


__all__ = ["AgentHarnessRuntime"]
