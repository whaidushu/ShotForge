from __future__ import annotations

from collections.abc import Callable

from shotforge.core.context_builder import ContextBuilder, ContextWindowPolicy
from shotforge.core.execution_policy import ExecutionPolicy
from shotforge.core.harness_snapshot import HarnessContextSnapshot
from shotforge.core.project_state import ProjectState
from shotforge.core.run_context import RunContext
from shotforge.core.trace_log import TraceLog
from shotforge.infra.mcp import MockMCPClient
from shotforge.infra.sandbox import SandboxPolicy
from shotforge.skills import SkillRegistry


class AgentHarnessRuntime:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        registry: SkillRegistry | None = None,
        execution_policy: ExecutionPolicy | None = None,
        sandbox_policy: SandboxPolicy | None = None,
        mcp_client: MockMCPClient | None = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.registry = registry or SkillRegistry()
        self.execution_policy = execution_policy or ExecutionPolicy()
        self.sandbox_policy = sandbox_policy or SandboxPolicy()
        self.mcp_client = mcp_client or MockMCPClient()

    def build_run_context(
        self,
        state: ProjectState,
        agent_name: str,
        tags: list[str] | None = None,
    ) -> RunContext:
        bundle = self.context_builder.build_bundle(
            state,
            agent_name,
            tags=tags,
            policy=ContextWindowPolicy(max_chars=self.execution_policy.max_context_chars),
        )
        return RunContext(
            run_id=state.run_id,
            project_id=state.project_id,
            version=state.version,
            agent_name=agent_name,
            language=state.language,
            context_bundle=bundle,
            skill_names=self.registry.names(),
            mcp_tool_names=[tool.name for tool in self.mcp_client.list_tools()],
            execution_policy=self.execution_policy.model_dump(mode="json"),
            sandbox_policy=self.sandbox_policy.model_dump(mode="json"),
        )

    def run_agent(
        self,
        state: ProjectState,
        agent_name: str,
        handler: Callable[[ProjectState], ProjectState],
        tags: list[str] | None = None,
    ) -> ProjectState:
        with TraceLog(state).span("agent_harness_runtime", agent_name=agent_name):
            run_context = self.build_run_context(state, agent_name, tags=tags)
            self._record_context(state, run_context)
            before_record_count = len(self.registry.records())
            result = handler(state)
            self._record_tool_calls(result, before_record_count)
            return result

    def _record_context(self, state: ProjectState, run_context: RunContext) -> None:
        bundle = run_context.context_bundle
        state.harness_contexts.append(
            HarnessContextSnapshot(
                agent_name=run_context.agent_name,
                source_count=len(bundle.sources) if bundle else 0,
                char_count=bundle.char_count if bundle else 0,
                source_types=[source.source_type for source in bundle.sources] if bundle else [],
                source_titles=[source.title for source in bundle.sources] if bundle else [],
                skill_count=len(run_context.skill_names),
                skill_names=run_context.skill_names,
                mcp_tool_count=len(run_context.mcp_tool_names),
                mcp_tool_names=run_context.mcp_tool_names,
                policy_id=self.execution_policy.policy_id,
                execution_policy=run_context.execution_policy,
                sandbox_policy=run_context.sandbox_policy,
                memory={"provider": "InMemoryStore", "status": "extension_ready", "hits": 0},
            )
        )

    def _record_tool_calls(self, state: ProjectState, before_record_count: int) -> None:
        records = self.registry.records()[before_record_count:]
        if not records:
            return
        state.tool_call_records.extend(records)


__all__ = ["AgentHarnessRuntime"]
