from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import (
    DeliveryReadinessReport,
    ProjectState,
    ReadinessCheck,
    ReadinessStatus,
)
from shotforge.core.trace_log import TraceLog
from shotforge.skills import SkillRegistry


def delivery_readiness_agent(
    state: ProjectState,
    context_builder: ContextBuilder,
    registry: SkillRegistry,
) -> ProjectState:
    with TraceLog(state).span("delivery_readiness_agent"):
        context_builder.build(
            state,
            "Delivery Readiness Agent",
            ["poc-readiness", "deployment", "governance"],
        )
        checks = [
            _state_schema_check(state),
            _context_observability_check(state),
            _tool_policy_check(state),
            _tool_orchestration_check(state),
            _state_transition_check(state),
            _agent_contract_check(state),
            _workflow_decision_check(state),
            _context_safety_check(state),
            _mcp_capability_check(state),
            _memory_strategy_check(state),
            _solution_architecture_check(state),
            _export_contract_check(registry),
            _provider_strategy_check(state),
            _evaluation_loop_check(state),
        ]
        state.delivery_readiness = DeliveryReadinessReport(
            overall_status=_overall_status(checks),
            checks=checks,
            handoff_deliverables=_handoff_deliverables(state),
            next_actions=_next_actions(state, checks),
            risk_register=_risk_register(state),
            metadata={
                "schema_version": "delivery_readiness_v1",
                "source": "delivery_readiness_agent",
                "passed": len([item for item in checks if item.status == "passed"]),
                "warnings": len([item for item in checks if item.status == "warning"]),
                "failed": len([item for item in checks if item.status == "failed"]),
            },
        )
    return state


def _state_schema_check(state: ProjectState) -> ReadinessCheck:
    passed = bool(state.creative_intent and state.shots and state.prompt_package.prompts)
    return ReadinessCheck(
        check_id="state_schema",
        category="State Management",
        status="passed" if passed else "failed",
        evidence=f"{len(state.shots)} shots, {len(state.prompt_package.prompts)} prompts, version v{state.version}",
        remediation="Generate intent, storyboard, motion, audio, and prompt package before handoff.",
    )


def _context_observability_check(state: ProjectState) -> ReadinessCheck:
    passed = bool(state.harness_contexts)
    return ReadinessCheck(
        check_id="context_observability",
        category="Context Engineering",
        status="passed" if passed else "failed",
        evidence=f"{len(state.harness_contexts)} context snapshots recorded",
        remediation="Enable AgentHarnessRuntime context snapshots for every agent.",
    )


def _tool_policy_check(state: ProjectState) -> ReadinessCheck:
    scopes = {record.permission_scope for record in state.tool_call_records}
    passed = bool(state.tool_call_records) and "local_file_write" in scopes
    return ReadinessCheck(
        check_id="tool_policy",
        category="Tool Orchestration",
        status="passed" if passed else "warning",
        evidence=f"{len(state.tool_call_records)} tool calls, scopes={sorted(scopes)}",
        remediation="Record permission scope and execution status for all production tools.",
    )


def _tool_orchestration_check(state: ProjectState) -> ReadinessCheck:
    failed = [
        record
        for record in state.tool_orchestration_records
        if record.status in {"failed", "denied", "fallback_failed"}
    ]
    fallback_used = [record for record in state.tool_orchestration_records if record.fallback_used]
    return ReadinessCheck(
        check_id="tool_orchestration",
        category="Tool Orchestration",
        status="passed" if state.tool_orchestration_records and not failed else "warning",
        evidence=(
            f"{len(state.tool_orchestration_records)} tool plans, "
            f"failed={len(failed)}, fallback_used={len(fallback_used)}"
        ),
        remediation="Review denied tools, schema failures, and fallback outcomes before pilot.",
    )


def _state_transition_check(state: ProjectState) -> ReadinessCheck:
    warnings = [
        issue
        for transition in state.state_transitions
        for issue in transition.invariant_issues
    ]
    return ReadinessCheck(
        check_id="state_transition_audit",
        category="State Management",
        status="passed" if state.state_transitions and not warnings else "warning",
        evidence=f"{len(state.state_transitions)} transitions, issues={len(warnings)}",
        remediation="Review state transition warnings before pilot handoff.",
    )


def _agent_contract_check(state: ProjectState) -> ReadinessCheck:
    failed = [
        report
        for report in state.agent_contract_reports
        if "failed" in {report.precondition_status, report.postcondition_status}
    ]
    return ReadinessCheck(
        check_id="agent_contracts",
        category="Agent Harness",
        status="passed" if state.agent_contract_reports and not failed else "warning",
        evidence=f"{len(state.agent_contract_reports)} contract reports, failed={len(failed)}",
        remediation="Review failed agent contracts before pilot handoff.",
    )


def _workflow_decision_check(state: ProjectState) -> ReadinessCheck:
    critical = [decision for decision in state.workflow_decisions if decision.severity == "critical"]
    return ReadinessCheck(
        check_id="workflow_decisions",
        category="Workflow Routing",
        status="passed" if state.workflow_decisions and not critical else "warning",
        evidence=f"{len(state.workflow_decisions)} routing decisions, critical={len(critical)}",
        remediation="Resolve critical workflow routing decisions before export.",
    )


def _context_safety_check(state: ProjectState) -> ReadinessCheck:
    redacted = [
        source_id
        for snapshot in state.harness_contexts
        for source_id in snapshot.metadata.get("redacted_sources", [])
    ]
    digests = [snapshot.metadata.get("context_digest") for snapshot in state.harness_contexts]
    return ReadinessCheck(
        check_id="context_safety",
        category="Context Engineering",
        status="passed" if all(digests) else "warning",
        evidence=f"{len(digests)} context digests, redacted_sources={len(redacted)}",
        remediation="Ensure every agent context has digest and redaction metadata.",
    )


def _mcp_capability_check(state: ProjectState) -> ReadinessCheck:
    tool_names = {
        tool_name
        for snapshot in state.harness_contexts
        for tool_name in snapshot.mcp_tool_names
    }
    required = {"knowledge.search", "runs.get_package", "runs.get_harness_audit"}
    missing = sorted(required - tool_names)
    return ReadinessCheck(
        check_id="mcp_capability",
        category="MCP",
        status="passed" if not missing else "warning",
        evidence=f"mcp_tools={sorted(tool_names)}, missing={missing}",
        remediation="Expose required MCP tools before external tool-host integration.",
    )


def _memory_strategy_check(state: ProjectState) -> ReadinessCheck:
    return ReadinessCheck(
        check_id="memory_strategy",
        category="Memory",
        status="passed" if state.memory_refs else "warning",
        evidence=f"memory_refs={len(state.memory_refs)}",
        remediation="Promote successful runs or seed customer memory before pilot.",
    )


def _solution_architecture_check(state: ProjectState) -> ReadinessCheck:
    architecture = state.solution_architecture
    passed = bool(
        architecture
        and architecture.components
        and architecture.integration_points
        and architecture.poc_success_criteria
    )
    return ReadinessCheck(
        check_id="solution_architecture",
        category="Solution Design",
        status="passed" if passed else "failed",
        evidence=(
            f"{len(architecture.components) if architecture else 0} components, "
            f"{len(architecture.integration_points) if architecture else 0} integrations"
        ),
        remediation="Generate customer-facing solution architecture before delivery.",
    )


def _export_contract_check(registry: SkillRegistry) -> ReadinessCheck:
    required = {
        "export.json",
        "export.csv",
        "export.markdown",
        "export.manifest",
        "export.trace",
        "export.run_summary",
    }
    available = set(registry.names())
    missing = sorted(required - available)
    return ReadinessCheck(
        check_id="export_contract",
        category="Delivery Package",
        status="passed" if not missing else "failed",
        evidence=f"available={sorted(required & available)}, missing={missing}",
        remediation="Register all required export skills.",
    )


def _provider_strategy_check(state: ProjectState) -> ReadinessCheck:
    provider = state.prompt_package.provider
    is_mock = "mock" in provider.lower()
    return ReadinessCheck(
        check_id="provider_strategy",
        category="Model Strategy",
        status="warning" if is_mock else "passed",
        evidence=f"prompt provider={provider}",
        remediation="Configure one real video provider and credentials for pilot.",
    )


def _evaluation_loop_check(state: ProjectState) -> ReadinessCheck:
    has_loop = bool(state.evaluation_reports or state.redesign_plans or state.verification_reports)
    return ReadinessCheck(
        check_id="evaluation_loop",
        category="Effect Evaluation",
        status="passed" if has_loop else "warning",
        evidence=(
            f"evaluations={len(state.evaluation_reports)}, "
            f"redesign_plans={len(state.redesign_plans)}, "
            f"verification_reports={len(state.verification_reports)}"
        ),
        remediation="Run full_loop or planning mode to produce evaluation and correction evidence.",
    )


def _overall_status(checks: list[ReadinessCheck]) -> ReadinessStatus:
    if any(item.status == "failed" and item.required_for_pilot for item in checks):
        return "failed"
    if any(item.status == "warning" for item in checks):
        return "warning"
    return "passed"


def _handoff_deliverables(state: ProjectState) -> list[str]:
    deliverables = [
        "ProjectState JSON package",
        "Storyboard CSV package",
        "Markdown production brief",
        "Harness Inspector trace",
        "Solution architecture summary",
        "Delivery readiness report",
    ]
    if state.evaluation_reports:
        deliverables.append("Evaluation report and issue list")
    if state.version_diffs:
        deliverables.append("Version diff and redesign evidence")
    return deliverables


def _next_actions(state: ProjectState, checks: list[ReadinessCheck]) -> list[str]:
    actions = [item.remediation for item in checks if item.status != "passed" and item.remediation]
    if state.solution_architecture:
        actions.append("Select one pilot customer scenario and bind success criteria to measurable data.")
    return actions


def _risk_register(state: ProjectState) -> list[str]:
    risks = [
        "External video model quality is not validated in mock mode.",
        "Customer asset ingestion and permission model are planned but not implemented.",
    ]
    if not state.evaluation_reports:
        risks.append("Quality loop evidence is absent until full_loop or planning mode runs.")
    return risks
