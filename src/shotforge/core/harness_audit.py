from __future__ import annotations

from typing import Any

from shotforge.core.project_state import ProjectState


def build_harness_audit(state: ProjectState | None) -> dict[str, Any]:
    if state is None:
        return {
            "contexts": [],
            "tool_calls": [],
            "tool_orchestration": [],
            "state_transitions": [],
            "agent_contracts": [],
            "workflow_decisions": [],
            "latest_context": {},
            "state_summary": {},
            "policies": {},
            "readiness": {},
            "solution": {},
            "agent_topology": {"nodes": [], "edges": []},
        }
    contexts = [item.model_dump(mode="json") for item in state.harness_contexts]
    tool_calls = [item.model_dump(mode="json") for item in state.tool_call_records]
    tool_orchestration = [
        item.model_dump(mode="json") for item in state.tool_orchestration_records
    ]
    state_transitions = [item.model_dump(mode="json") for item in state.state_transitions]
    agent_contracts = [item.model_dump(mode="json") for item in state.agent_contract_reports]
    workflow_decisions = [item.model_dump(mode="json") for item in state.workflow_decisions]
    latest_context = contexts[-1] if contexts else {}
    return {
        "project_id": state.project_id,
        "run_id": state.run_id,
        "version": state.version,
        "contexts": contexts,
        "tool_calls": tool_calls,
        "tool_orchestration": tool_orchestration,
        "state_transitions": state_transitions,
        "agent_contracts": agent_contracts,
        "workflow_decisions": workflow_decisions,
        "latest_context": latest_context,
        "agent_topology": _agent_topology(contexts, state_transitions),
        "policies": {
            "execution": latest_context.get("execution_policy", {}),
            "sandbox": latest_context.get("sandbox_policy", {}),
            "mcp_tool_names": latest_context.get("mcp_tool_names", []),
            "memory": latest_context.get("memory", {}),
        },
        "state_summary": {
            "trace_events": len(state.trace_logs),
            "tool_calls": len(state.tool_call_records),
            "tool_orchestration": len(state.tool_orchestration_records),
            "state_transitions": len(state.state_transitions),
            "agent_contracts": len(state.agent_contract_reports),
            "workflow_decisions": len(state.workflow_decisions),
            "knowledge_refs": len(state.knowledge_refs),
            "memory_refs": len(state.memory_refs),
            "evaluations": len(state.evaluation_reports),
            "corrections": len(state.correction_patches),
            "exports": [item.model_dump(mode="json") for item in state.exports],
        },
        "readiness": _readiness_summary(state),
        "solution": _solution_summary(state),
    }


def _readiness_summary(state: ProjectState) -> dict[str, Any]:
    if state.delivery_readiness is None:
        return {}
    report = state.delivery_readiness
    return {
        "overall_status": report.overall_status,
        "checks": [item.model_dump(mode="json") for item in report.checks],
        "handoff_deliverables": report.handoff_deliverables,
        "next_actions": report.next_actions,
        "risk_register": report.risk_register,
    }


def _solution_summary(state: ProjectState) -> dict[str, Any]:
    if state.solution_architecture is None:
        return {}
    solution = state.solution_architecture
    return {
        "industry": solution.industry,
        "scenario": solution.scenario,
        "business_objective": solution.business_objective,
        "knowledge_assets": solution.knowledge_assets,
        "scenario_patterns": solution.scenario_patterns,
        "evaluation_metrics": solution.evaluation_metrics,
        "poc_success_criteria": [
            item.model_dump(mode="json") for item in solution.poc_success_criteria
        ],
    }


def _agent_topology(
    contexts: list[dict[str, Any]],
    transitions: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes = []
    seen = set()
    for context in contexts:
        agent_name = context.get("agent_name", "")
        if not agent_name or agent_name in seen:
            continue
        seen.add(agent_name)
        spec = context.get("metadata", {}).get("agent_spec", {})
        nodes.append(
            {
                "agent_name": agent_name,
                "role": spec.get("role", ""),
                "inputs": spec.get("inputs", []),
                "outputs": spec.get("outputs", []),
            }
        )

    ordered_agents = [item.get("agent_name") for item in transitions if item.get("agent_name")]
    edges = [
        {"from": ordered_agents[index], "to": ordered_agents[index + 1]}
        for index in range(len(ordered_agents) - 1)
    ]
    return {"nodes": nodes, "edges": edges}
