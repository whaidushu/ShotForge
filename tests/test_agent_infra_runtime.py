from pathlib import Path

import pytest

from shotforge.agents import AgentHarness, build_default_agent_catalog, build_default_registry
from shotforge.core.context_builder import ContextBuildPolicy, ContextBuilder
from shotforge.core.harness_runtime import AgentHarnessRuntime
from shotforge.core.project_state import ProjectState
from shotforge.infra.mcp import LocalMCPAdapter
from shotforge.infra.memory import LocalMemoryStore
from shotforge.infra.policies import ExecutionPolicy
from shotforge.infra.sandbox import LocalSandboxRunner, SandboxExecutionProfile, SandboxPolicy
from shotforge.skills import SkillRegistry, ToolExecutionPolicy
from shotforge.workflows.design_workflow import build_design_graph, run_design_pipeline


def test_agent_harness_runtime_records_context_and_tool_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A quiet revenge reveal in a luxury elevator", language="en")

    assert state.harness_contexts
    assert {item.agent_name for item in state.harness_contexts} >= {
        "intent_agent",
        "delivery_readiness_agent",
        "solution_architect_agent",
        "storyboard_agent",
        "export_agent",
    }
    assert any("knowledge.search" in item.mcp_tool_names for item in state.harness_contexts)
    assert state.solution_architecture is not None
    assert state.delivery_readiness is not None
    assert state.tool_call_records
    assert state.tool_orchestration_records
    assert state.state_transitions
    assert state.agent_contract_reports
    assert state.workflow_decisions
    assert any(
        item.agent_name == "prompt_adapter_agent" and "prompts" in item.changed_fields
        for item in state.state_transitions
    )
    assert all(item.precondition_status == "passed" for item in state.agent_contract_reports)
    assert all(item.postcondition_status == "passed" for item in state.agent_contract_reports)
    assert any(
        decision.agent_name == "delivery_readiness_agent" and decision.decision == "review"
        for decision in state.workflow_decisions
    )
    assert all(item.invariant_status == "passed" for item in state.state_transitions)
    assert any(record.tool_name == "mock_llm.complete" for record in state.tool_call_records)
    assert any(
        record.requested_tool == "mock_llm.complete" and record.schema_status == "passed"
        for record in state.tool_orchestration_records
    )
    assert any(
        record.agent_name == "export_agent" and record.expected_output == "json package"
        for record in state.tool_orchestration_records
    )
    assert any(record.permission_scope == "local_file_write" for record in state.tool_call_records)
    assert all(snapshot.metadata.get("context_digest") for snapshot in state.harness_contexts)
    assert all(snapshot.metadata.get("agent_spec") for snapshot in state.harness_contexts)
    assert any("project_state" in snapshot.source_types for snapshot in state.harness_contexts)


def test_context_builder_ranks_sources_and_enforces_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = ProjectState(
        user_idea="A " + "very detailed cinematic production idea " * 20,
        language="en",
    )
    builder = ContextBuilder(policy=ContextBuildPolicy(max_chars=760))

    context = builder.build(state, "Intent Agent", tags=["cinematic"])

    assert context.digest
    assert context.sources[0].source_id == "user_goal"
    assert context.sources[1].source_id == "project_state"
    assert context.char_count <= context.max_chars
    assert any(source.truncated or not source.included for source in context.sources)
    assert "Context Sources" in context.as_prompt()


def test_context_builder_redacts_sensitive_terms(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = ProjectState(user_idea="Create video with token=abc123 and secret:xyz789", language="en")

    context = ContextBuilder().build(state, "Intent Agent")
    prompt = context.as_prompt()

    assert "abc123" not in prompt
    assert "xyz789" not in prompt
    assert "[REDACTED]" in prompt
    assert any(source.redacted for source in context.sources)


def test_default_agent_catalog_exposes_topology():
    catalog = build_default_agent_catalog()
    spec = catalog.get("prompt_adapter_agent")
    edges = catalog.dependency_edges()

    assert spec.outputs == ["prompt_package"]
    assert "provider_prompt_adapter" in spec.extension_points
    assert {"from": "audio_cue_agent", "to": "prompt_adapter_agent"} in edges


def test_runtime_injects_memory_hits_into_context(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    memory = LocalMemoryStore(tmp_path / "memory.jsonl")
    record = memory.add(
        "User prefers quiet revenge stories with high-contrast noir framing.",
        tags=["cinematic", "visual"],
        source_run_id="previous_run",
    )
    registry = build_default_registry()
    runtime = AgentHarnessRuntime(
        registry=registry,
        memory_store=memory,
        execution_policy=ExecutionPolicy(max_context_chars=3000),
    )
    harness = AgentHarness(registry=registry, runtime=runtime)
    state = ProjectState(user_idea="quiet revenge", language="en")
    result = build_design_graph(harness).invoke({"project": state})["project"]

    assert record.memory_id in result.memory_refs
    assert any(snapshot.memory["hits"] >= 1 for snapshot in result.harness_contexts)


def test_runtime_enforces_agent_tool_call_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    registry = SkillRegistry()
    registry.register("local.echo", lambda purpose="": "ok")
    runtime = AgentHarnessRuntime(
        registry=registry,
        execution_policy=ExecutionPolicy(max_tool_calls_per_agent=0),
    )
    state = ProjectState(user_idea="budget test", language="en")

    with pytest.raises(PermissionError):
        runtime.run_agent(
            state,
            "budget_agent",
            lambda project: (registry.call("local.echo", purpose="budget"), project)[1],
        )

    assert any(record.tool_name == "agent_harness.tool_budget" for record in state.tool_call_records)


def test_runtime_blocks_agent_when_contract_preconditions_fail(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    runtime = AgentHarnessRuntime()
    state = ProjectState(user_idea="contract test", language="en")

    with pytest.raises(PermissionError):
        runtime.run_agent(
            state,
            "storyboard_agent",
            lambda project: project,
        )

    assert state.agent_contract_reports[-1].agent_name == "storyboard_agent"
    assert state.agent_contract_reports[-1].precondition_status == "failed"
    assert "creative_intent" in state.agent_contract_reports[-1].missing_inputs
    assert state.workflow_decisions[-1].decision == "block"
    assert state.workflow_decisions[-1].severity == "critical"


def test_memory_store_ranks_updates_and_promotes_runs(tmp_path):
    memory = LocalMemoryStore(tmp_path / "memory.jsonl")
    low = memory.add(
        "generic cinematic note",
        tags=["cinematic"],
        namespace="demo",
        importance=0.1,
    )
    high = memory.add(
        "quiet revenge noir framing with readable silhouette",
        tags=["cinematic", "noir"],
        namespace="demo",
        importance=0.9,
    )

    results = memory.search("quiet revenge", tags=["cinematic"], namespace="demo", limit=2)
    promoted = memory.promote_run(
        run_id="run_1",
        summary="successful noir revenge package",
        tags=["noir"],
        namespace="demo",
    )

    reloaded = {record.memory_id: record for record in memory._load()}
    assert results[0].memory_id == high.memory_id
    assert low.memory_id not in [record.memory_id for record in memory.search("quiet revenge")]
    assert reloaded[high.memory_id].access_count == 1
    assert reloaded[high.memory_id].last_accessed_at is not None
    assert promoted.kind == "promoted_run"
    assert promoted.source_run_id == "run_1"


def test_runtime_promotes_exported_run_into_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    memory = LocalMemoryStore(tmp_path / "memory.jsonl")
    registry = build_default_registry()
    runtime = AgentHarnessRuntime(registry=registry, memory_store=memory)
    harness = AgentHarness(registry=registry, runtime=runtime)
    state = ProjectState(user_idea="A neon train crossing a desert", language="en")

    result = build_design_graph(harness).invoke({"project": state})["project"]
    hits = memory.search("neon train", tags=["cinematic"], namespace="shotforge")

    assert result.metadata["memory_promoted_run_id"] == result.run_id
    assert hits
    assert hits[0].source_run_id == result.run_id
    assert hits[0].kind == "promoted_run"


def test_local_mcp_adapter_exposes_tools_and_resources(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A neon train crossing a desert at sunrise", language="en")
    mcp = LocalMCPAdapter()

    tools = {tool.name for tool in mcp.list_tools()}
    search_result = mcp.call_tool("knowledge.search", {"query": "prompt", "limit": 2})
    package_result = mcp.call_tool("runs.get_package", {"run_id": state.run_id})
    harness_result = mcp.call_tool("runs.get_harness_audit", {"run_id": state.run_id})
    resource_uri = f"shotforge://runs/{state.run_id}/package"
    harness_uri = f"shotforge://runs/{state.run_id}/harness"
    resources = {resource.uri for resource in mcp.list_resources()}
    capabilities = mcp.capabilities()

    assert {"knowledge.search", "runs.list", "runs.get_package", "runs.get_harness_audit"}.issubset(
        tools
    )
    assert capabilities["server"]["name"] == "shotforge-local-mcp"
    assert resource_uri in resources
    assert harness_uri in resources
    assert search_result.result["items"]
    assert package_result.result["package"]["run_id"] == state.run_id
    assert harness_result.result["harness_audit"]["run_id"] == state.run_id
    assert mcp.read_resource(resource_uri)["run_id"] == state.run_id
    assert mcp.read_resource(harness_uri)["run_id"] == state.run_id


def test_local_sandbox_runner_enforces_policy(tmp_path):
    sandbox = LocalSandboxRunner(
        SandboxPolicy(
            dry_run=False,
            allowed_commands=["python"],
            working_dir=Path(tmp_path),
            max_timeout_seconds=5,
        )
    )

    result = sandbox.run(["python", "--version"], timeout_seconds=5)

    assert result.status == "completed"
    assert result.exit_code == 0
    assert result.profile_id == "local_python_readonly"
    assert result.policy_decision == "allowed"
    assert result.working_dir == str(tmp_path)
    with pytest.raises(PermissionError):
        sandbox.run(["powershell", "-Command", "Write-Output nope"])


def test_local_sandbox_runner_can_return_structured_denial(tmp_path):
    sandbox = LocalSandboxRunner(
        SandboxPolicy(
            dry_run=True,
            allowed_commands=["python"],
            working_dir=Path(tmp_path),
            execution_profile=SandboxExecutionProfile(profile_id="demo_profile"),
        )
    )

    result = sandbox.run(["powershell", "-Command", "nope"], raise_on_policy_violation=False)

    assert result.status == "denied"
    assert result.profile_id == "demo_profile"
    assert result.policy_decision == "denied"
    assert "not allowed" in result.policy_reason


def test_skill_registry_denies_unauthorized_tool_scope():
    registry = SkillRegistry(
        policy=ToolExecutionPolicy(
            allowed_permission_scopes={"local"},
            max_total_calls=2,
            max_calls_per_tool=1,
        )
    )
    registry.register(
        "external.call",
        lambda: "ok",
        permission_scope="external_network",
        risk_level="high",
    )

    with pytest.raises(PermissionError):
        registry.call("external.call", purpose="test")

    record = registry.records()[-1]
    assert record.status == "failed"
    assert record.permission_scope == "external_network"
    assert record.metadata["authorized"] is False
    assert record.metadata["risk_level"] == "high"
    orchestration = registry.orchestration_records()[-1]
    assert orchestration.status == "denied"
    assert orchestration.authorization_decision == "denied"
    assert "permission_scope_denied:external_network" in orchestration.authorization_reasons


def test_skill_registry_records_authorized_tool_metadata():
    registry = SkillRegistry(policy=ToolExecutionPolicy(max_calls_per_tool=1))
    registry.register("local.echo", lambda value, purpose="": value, description="Echo input")

    assert registry.call("local.echo", "ok", purpose="unit_test") == "ok"
    with pytest.raises(PermissionError):
        registry.call("local.echo", "blocked", purpose="unit_test")

    records = registry.records()
    assert records[0].metadata["authorized"] is True
    assert records[0].metadata["purpose"] == "unit_test"
    assert records[1].metadata["authorized"] is False
    assert registry.call_counts()["local.echo"] == 1


def test_skill_registry_schema_failure_can_fallback():
    registry = SkillRegistry()
    registry.register(
        "primary.bad",
        lambda value: 123,
        input_schema={"required_arg_count": 1},
        output_schema={"type": "str"},
    )
    registry.register(
        "fallback.good",
        lambda value: f"ok:{value}",
        input_schema={"required_arg_count": 1},
        output_schema={"type": "str"},
    )

    result = registry.call(
        "primary.bad",
        "demo",
        agent_name="unit_agent",
        expected_output="string result",
        fallback_tools=["fallback.good"],
    )

    assert result == "ok:demo"
    record = registry.orchestration_records()[-1]
    assert record.status == "fallback_completed"
    assert record.fallback_used is True
    assert record.selected_tool == "fallback.good"
    assert record.attempted_tools == ["primary.bad", "fallback.good"]
    assert record.schema_status == "failed"
    assert record.schema_issues
