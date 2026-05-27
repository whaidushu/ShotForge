from shotforge.agents import AgentHarness, build_default_registry
from shotforge.core.context_builder import ContextBuilder
from shotforge.core.execution_policy import ExecutionPolicy
from shotforge.core.harness_runtime import AgentHarnessRuntime
from shotforge.core.memory import InMemoryStore
from shotforge.core.project_state import ProjectState
from shotforge.infra.mcp import MockMCPClient
from shotforge.infra.sandbox import LocalSandbox, SandboxPolicy
from shotforge.workflows.design_workflow import build_design_graph, run_design_pipeline


def test_context_builder_outputs_structured_context_bundle(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = ProjectState(user_idea="A quiet revenge reveal", language="en")
    bundle = ContextBuilder().build_bundle(state, "intent_agent", tags=["intent"])

    assert bundle.agent_name == "intent_agent"
    assert {source.source_type for source in bundle.sources} >= {"user_goal", "project_state"}
    assert bundle.char_count <= bundle.policy.max_chars


def test_skill_registry_records_tool_calls():
    registry = build_default_registry()

    result = registry.call("mock_llm.complete", "hello", purpose="test")
    records = registry.records()

    assert result
    assert records
    assert records[-1].tool_name == "mock_llm.complete"
    assert records[-1].status == "completed"
    assert registry.spec("mock_llm.complete").permission_scope == "local_inference"


def test_agent_harness_runtime_records_context_and_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A quiet revenge reveal in a luxury elevator", language="en")

    assert state.harness_contexts
    assert any(item.agent_name == "intent_agent" for item in state.harness_contexts)
    assert state.tool_call_records
    assert any(record.tool_name == "mock_llm.complete" for record in state.tool_call_records)


def test_runtime_can_be_injected_into_langgraph_design_graph(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    registry = build_default_registry()
    runtime = AgentHarnessRuntime(
        registry=registry,
        execution_policy=ExecutionPolicy(max_context_chars=3000),
        mcp_client=MockMCPClient(),
    )
    harness = AgentHarness(registry=registry, runtime=runtime)
    state = ProjectState(user_idea="A neon train crossing a desert", language="en")
    result = build_design_graph(harness).invoke({"project": state})["project"]

    assert result.harness_contexts
    assert all(item.policy_id == "default_agent_harness_policy" for item in result.harness_contexts)


def test_mock_mcp_memory_and_sandbox_contracts():
    mcp = MockMCPClient()
    memory = InMemoryStore()
    sandbox = LocalSandbox(SandboxPolicy(dry_run=True))

    memory.add("User prefers high-contrast noir framing.", tags=["style"])
    sandbox_result = sandbox.run("noop", lambda: "done")

    assert "knowledge.search" in {tool.name for tool in mcp.list_tools()}
    assert memory.search(tags=["style"])[0].content.startswith("User prefers")
    assert sandbox_result.status == "dry_run"
