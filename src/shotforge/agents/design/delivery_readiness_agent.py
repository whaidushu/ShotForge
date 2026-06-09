from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import (
    DeliveryReadinessReport,
    ProjectState,
    ReadinessCheck,
    ReadinessStatus,
    runtime_language,
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
            ["acceptance-readiness", "deployment", "governance"],
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
            _sandbox_strategy_check(state),
            _solution_architecture_check(state),
            _export_contract_check(state, registry),
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
        category=_text(state, "State Management", "状态管理"),
        status="passed" if passed else "failed",
        evidence=_text(
            state,
            f"{len(state.shots)} shots, {len(state.prompt_package.prompts)} prompts, version v{state.version}",
            f"{len(state.shots)} 个镜头，{len(state.prompt_package.prompts)} 条提示词，版本 v{state.version}",
        ),
        remediation=_text(
            state,
            "Generate intent, storyboard, motion, audio, and prompt package before handoff.",
            "交付前先生成意图、分镜、运动、音频和提示词任务包。",
        ),
    )


def _context_observability_check(state: ProjectState) -> ReadinessCheck:
    passed = bool(state.harness_contexts)
    return ReadinessCheck(
        check_id="context_observability",
        category=_text(state, "Context Engineering", "上下文工程"),
        status="passed" if passed else "failed",
        evidence=_text(
            state,
            f"{len(state.harness_contexts)} context snapshots recorded",
            f"已记录 {len(state.harness_contexts)} 份上下文快照",
        ),
        remediation=_text(
            state,
            "Enable AgentHarnessRuntime context snapshots for every agent.",
            "为每个 Agent 启用 AgentHarnessRuntime 上下文快照。",
        ),
    )


def _tool_policy_check(state: ProjectState) -> ReadinessCheck:
    scopes = {record.permission_scope for record in state.tool_call_records}
    passed = bool(state.tool_call_records) and "local_file_write" in scopes
    return ReadinessCheck(
        check_id="tool_policy",
        category=_text(state, "Tool Orchestration", "工具编排"),
        status="passed" if passed else "warning",
        evidence=_text(
            state,
            f"{len(state.tool_call_records)} tool calls, scopes={sorted(scopes)}",
            f"{len(state.tool_call_records)} 次工具调用，权限范围={sorted(scopes)}",
        ),
        remediation=_text(
            state,
            "Record permission scope and execution status for all production tools.",
            "为所有生产工具记录权限范围和执行状态。",
        ),
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
        category=_text(state, "Tool Orchestration", "工具编排"),
        status="passed" if state.tool_orchestration_records and not failed else "warning",
        evidence=_text(
            state,
            (
                f"{len(state.tool_orchestration_records)} tool plans, "
                f"failed={len(failed)}, fallback_used={len(fallback_used)}"
            ),
            (
                f"{len(state.tool_orchestration_records)} 条工具计划，"
                f"失败={len(failed)}，使用降级={len(fallback_used)}"
            ),
        ),
        remediation=_text(
            state,
            "Review denied tools, schema failures, and fallback outcomes before pilot.",
            "试点前复核被拒绝工具、schema 失败和降级结果。",
        ),
    )


def _state_transition_check(state: ProjectState) -> ReadinessCheck:
    warnings = [
        issue
        for transition in state.state_transitions
        for issue in transition.invariant_issues
    ]
    return ReadinessCheck(
        check_id="state_transition_audit",
        category=_text(state, "State Management", "状态管理"),
        status="passed" if state.state_transitions and not warnings else "warning",
        evidence=_text(
            state,
            f"{len(state.state_transitions)} transitions, issues={len(warnings)}",
            f"{len(state.state_transitions)} 次状态变化，问题={len(warnings)}",
        ),
        remediation=_text(
            state,
            "Review state transition warnings before pilot handoff.",
            "试点交付前复核状态变化告警。",
        ),
    )


def _agent_contract_check(state: ProjectState) -> ReadinessCheck:
    failed = [
        report
        for report in state.agent_contract_reports
        if "failed" in {report.precondition_status, report.postcondition_status}
    ]
    return ReadinessCheck(
        check_id="agent_contracts",
        category=_text(state, "Agent Harness", "Agent Harness"),
        status="passed" if state.agent_contract_reports and not failed else "warning",
        evidence=_text(
            state,
            f"{len(state.agent_contract_reports)} contract reports, failed={len(failed)}",
            f"{len(state.agent_contract_reports)} 份契约报告，失败={len(failed)}",
        ),
        remediation=_text(
            state,
            "Review failed agent contracts before pilot handoff.",
            "试点交付前复核失败的 Agent 契约。",
        ),
    )


def _workflow_decision_check(state: ProjectState) -> ReadinessCheck:
    critical = [decision for decision in state.workflow_decisions if decision.severity == "critical"]
    gate_counts = [
        decision.metadata.get("gate_counts", {})
        for decision in state.workflow_decisions
        if decision.metadata.get("gate_counts")
    ]
    return ReadinessCheck(
        check_id="workflow_decisions",
        category=_text(state, "Workflow Routing", "工作流路由"),
        status="passed" if state.workflow_decisions and not critical else "warning",
        evidence=_text(
            state,
            (
                f"{len(state.workflow_decisions)} routing decisions, "
                f"critical={len(critical)}, gate_snapshots={len(gate_counts)}"
            ),
            (
                f"{len(state.workflow_decisions)} 条路由决策，"
                f"严重={len(critical)}，门禁快照={len(gate_counts)}"
            ),
        ),
        remediation=_text(
            state,
            "Resolve critical workflow routing decisions before export.",
            "导出前处理严重的工作流路由决策。",
        ),
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
        category=_text(state, "Context Engineering", "上下文工程"),
        status="passed" if all(digests) else "warning",
        evidence=_text(
            state,
            f"{len(digests)} context digests, redacted_sources={len(redacted)}",
            f"{len(digests)} 份上下文摘要，脱敏来源={len(redacted)}",
        ),
        remediation=_text(
            state,
            "Ensure every agent context has digest and redaction metadata.",
            "确保每个 Agent 上下文都有摘要和脱敏元数据。",
        ),
    )


def _mcp_capability_check(state: ProjectState) -> ReadinessCheck:
    tool_names = {
        tool_name
        for snapshot in state.harness_contexts
        for tool_name in snapshot.mcp_tool_names
    }
    required = {"knowledge.search", "runs.get_package", "runs.get_harness_audit"}
    missing = sorted(required - tool_names)
    denied = [record for record in state.mcp_access_records if record.status == "denied"]
    return ReadinessCheck(
        check_id="mcp_capability",
        category="MCP",
        status="passed" if not missing and not denied else "warning",
        evidence=_text(
            state,
            (
                f"mcp_tools={sorted(tool_names)}, missing={missing}, "
                f"access_records={len(state.mcp_access_records)}, denied={len(denied)}"
            ),
            (
                f"MCP 工具={sorted(tool_names)}，缺失={missing}，"
                f"访问记录={len(state.mcp_access_records)}，拒绝={len(denied)}"
            ),
        ),
        remediation=_text(
            state,
            "Expose required MCP tools before external tool-host integration.",
            "对接外部工具宿主前暴露所需 MCP 工具。",
        ),
    )


def _memory_strategy_check(state: ProjectState) -> ReadinessCheck:
    promotions = [
        record
        for record in state.memory_selection_records
        if record.promotion_decision in {"promote", "skip"}
    ]
    return ReadinessCheck(
        check_id="memory_strategy",
        category=_text(state, "Memory", "记忆"),
        status="passed" if state.memory_selection_records else "warning",
        evidence=_text(
            state,
            (
                f"memory_refs={len(state.memory_refs)}, "
                f"selection_records={len(state.memory_selection_records)}, "
                f"promotion_decisions={len(promotions)}"
            ),
            (
                f"记忆引用={len(state.memory_refs)}，"
                f"选择记录={len(state.memory_selection_records)}，"
                f"沉淀决策={len(promotions)}"
            ),
        ),
        remediation=_text(
            state,
            "Promote successful runs or seed customer memory before pilot.",
            "试点前沉淀成功任务或初始化客户场景记忆。",
        ),
    )


def _sandbox_strategy_check(state: ProjectState) -> ReadinessCheck:
    denied = [record for record in state.sandbox_policy_records if record.decision == "denied"]
    boundary_snapshots = [
        record
        for record in state.sandbox_policy_records
        if record.metadata.get("require_workspace_boundary")
    ]
    return ReadinessCheck(
        check_id="sandbox_strategy",
        category="Sandbox",
        status="passed" if state.sandbox_policy_records and not denied else "warning",
        evidence=_text(
            state,
            (
                f"{len(state.sandbox_policy_records)} sandbox records, "
                f"denied={len(denied)}, boundary_snapshots={len(boundary_snapshots)}"
            ),
            (
                f"{len(state.sandbox_policy_records)} 条 Sandbox 记录，"
                f"拒绝={len(denied)}，边界快照={len(boundary_snapshots)}"
            ),
        ),
        remediation=_text(
            state,
            "Review denied sandbox activity and enforce workspace boundary before pilot.",
            "试点前复核被拒绝的 Sandbox 活动，并强制工作区边界。",
        ),
    )


def _solution_architecture_check(state: ProjectState) -> ReadinessCheck:
    architecture = state.solution_architecture
    passed = bool(
        architecture
        and architecture.components
        and architecture.integration_points
        and architecture.acceptance_criteria
    )
    return ReadinessCheck(
        check_id="solution_architecture",
        category=_text(state, "Solution Design", "方案设计"),
        status="passed" if passed else "failed",
        evidence=_text(
            state,
            (
                f"{len(architecture.components) if architecture else 0} components, "
                f"{len(architecture.integration_points) if architecture else 0} integrations"
            ),
            (
                f"{len(architecture.components) if architecture else 0} 个组件，"
                f"{len(architecture.integration_points) if architecture else 0} 个集成点"
            ),
        ),
        remediation=_text(
            state,
            "Generate customer-facing solution architecture before delivery.",
            "交付前生成面向客户的解决方案架构。",
        ),
    )


def _export_contract_check(state: ProjectState, registry: SkillRegistry) -> ReadinessCheck:
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
        category=_text(state, "Delivery Package", "交付任务包"),
        status="passed" if not missing else "failed",
        evidence=_text(
            state,
            f"available={sorted(required & available)}, missing={missing}",
            f"可用={sorted(required & available)}，缺失={missing}",
        ),
        remediation=_text(
            state,
            "Register all required export skills.",
            "注册全部必需的导出 Skill。",
        ),
    )


def _provider_strategy_check(state: ProjectState) -> ReadinessCheck:
    provider = state.prompt_package.provider
    is_mock = "mock" in provider.lower()
    return ReadinessCheck(
        check_id="provider_strategy",
        category=_text(state, "Model Strategy", "模型策略"),
        status="warning" if is_mock else "passed",
        evidence=_text(state, f"prompt provider={provider}", f"提示词服务={provider}"),
        remediation=_text(
            state,
            "Configure one real video provider and credentials for pilot.",
            "为试点配置一个真实视频生成服务和凭证。",
        ),
    )


def _evaluation_loop_check(state: ProjectState) -> ReadinessCheck:
    has_loop = bool(state.evaluation_reports or state.redesign_plans or state.verification_reports)
    return ReadinessCheck(
        check_id="evaluation_loop",
        category=_text(state, "Effect Evaluation", "效果评估"),
        status="passed" if has_loop else "warning",
        evidence=_text(
            state,
            (
                f"evaluations={len(state.evaluation_reports)}, "
                f"redesign_plans={len(state.redesign_plans)}, "
                f"verification_reports={len(state.verification_reports)}"
            ),
            (
                f"评估={len(state.evaluation_reports)}，"
                f"重设计计划={len(state.redesign_plans)}，"
                f"验证报告={len(state.verification_reports)}"
            ),
        ),
        remediation=_text(
            state,
            "Run full_loop or planning mode to produce evaluation and correction evidence.",
            "运行 full_loop 或 planning 模式，生成评估与修正证据。",
        ),
    )


def _overall_status(checks: list[ReadinessCheck]) -> ReadinessStatus:
    if any(item.status == "failed" and item.required_for_pilot for item in checks):
        return "failed"
    if any(item.status == "warning" for item in checks):
        return "warning"
    return "passed"


def _handoff_deliverables(state: ProjectState) -> list[str]:
    deliverables = [
        _text(state, "ProjectState JSON package", "ProjectState JSON 任务包"),
        _text(state, "Storyboard CSV package", "分镜 CSV 任务包"),
        _text(state, "Markdown production brief", "Markdown 生产简报"),
        _text(state, "Harness evidence trace", "Harness 证据链路"),
        _text(state, "Solution architecture summary", "解决方案架构摘要"),
        _text(state, "Delivery readiness report", "交付就绪度报告"),
    ]
    if state.evaluation_reports:
        deliverables.append(_text(state, "Evaluation report and issue list", "评估报告与问题清单"))
    if state.version_diffs:
        deliverables.append(_text(state, "Version diff and redesign evidence", "版本差异与重设计证据"))
    return deliverables


def _next_actions(state: ProjectState, checks: list[ReadinessCheck]) -> list[str]:
    actions = [item.remediation for item in checks if item.status != "passed" and item.remediation]
    if state.solution_architecture:
        actions.append(
            _text(
                state,
                "Select one pilot customer scenario and bind success criteria to measurable data.",
                "选择一个试点客户场景，并将成功标准绑定到可度量数据。",
            )
        )
    return actions


def _risk_register(state: ProjectState) -> list[str]:
    risks = [
        _text(
            state,
            "External video model quality is not validated in test mode.",
            "测试模式下尚未验证外部视频模型质量。",
        ),
        _text(
            state,
            "Customer asset ingestion and permission model are planned but not implemented.",
            "客户资产接入和权限模型仍处于规划阶段，尚未实现。",
        ),
    ]
    if not state.evaluation_reports:
        risks.append(
            _text(
                state,
                "Quality loop evidence is absent until full_loop or planning mode runs.",
                "在运行 full_loop 或 planning 模式前，质量闭环证据仍然缺失。",
            )
        )
    return risks


def _text(state: ProjectState, en: str, zh: str) -> str:
    return zh if runtime_language(state) == "zh" else en
