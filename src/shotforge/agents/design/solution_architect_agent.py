from __future__ import annotations

from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import (
    ArchitectureComponent,
    IntegrationPoint,
    POCSuccessCriterion,
    ProjectState,
    RolloutPhase,
    SolutionArchitecture,
    ValueMetric,
)
from shotforge.core.solution_playbook import SolutionPlaybook, SolutionPlaybookStore
from shotforge.core.trace_log import TraceLog
from shotforge.skills import SkillRegistry


def solution_architect_agent(
    state: ProjectState,
    context_builder: ContextBuilder,
    registry: SkillRegistry,
) -> ProjectState:
    with TraceLog(state).span("solution_architect_agent"):
        context = context_builder.build(
            state,
            "Solution Architect Agent",
            ["solution-design", "agent-infra", "customer-value"],
        )
        completion = registry.call(
            "mock_llm.complete",
            context.as_prompt(),
            purpose="solution_architecture",
        )
        industry, scenario = _infer_industry_and_scenario(state.user_idea, state.language)
        playbook = SolutionPlaybookStore().find_for_industry(_canonical_industry(industry))
        state.solution_architecture = SolutionArchitecture(
            industry=industry,
            scenario=scenario,
            business_objective=_text(
                state,
                "Reduce creative planning latency and make video prompt production auditable.",
                "\u964d\u4f4e\u521b\u610f\u7b56\u5212\u5230\u89c6\u9891\u63d0\u793a\u8bcd\u751f\u4ea7\u7684\u8017\u65f6\uff0c\u5e76\u8ba9\u751f\u4ea7\u8fc7\u7a0b\u53ef\u8ffd\u6eaf\u3001\u53ef\u8bc4\u4f30\u3002",
            ),
            reference_customer=_text(
                state,
                "Brand marketing, content studio, or AI video operations team",
                "\u54c1\u724c\u8425\u9500\u3001\u5185\u5bb9\u5de5\u4f5c\u5ba4\u6216 AI \u89c6\u9891\u8fd0\u8425\u56e2\u961f",
            ),
            model_strategy=_text(
                state,
                "Mock LLM in POC, pluggable video providers for ComfyUI/Jimeng/Kling/Runway/Open-Sora.",
                "POC \u9636\u6bb5\u4f7f\u7528 Mock LLM\uff0c\u4fdd\u7559 ComfyUI/\u5373\u68a6/Kling/Runway/Open-Sora \u7684\u53ef\u63d2\u62d4\u89c6\u9891\u6a21\u578b\u9002\u914d\u3002",
            ),
            agent_topology=[
                "Intent -> Storyboard -> Motion -> Audio Cue -> Prompt Adapter -> Solution Architect -> Export",
                "Evaluation loop can add Mock Generation -> Multi-signal Evaluation -> Correction Router -> Redesign -> Verification",
            ],
            components=_components(state),
            integration_points=_integration_points(state, playbook),
            safety_controls=_safety_controls(state, playbook),
            poc_success_criteria=_success_criteria(state, playbook),
            rollout_plan=_rollout_plan(state),
            value_metrics=_value_metrics(state, playbook),
            knowledge_assets=[
                playbook.playbook_id,
                "evaluation_rubrics.json",
                "prompt_rules.json",
                "correction_strategies.json",
            ],
            scenario_patterns=playbook.scenario_patterns,
            evaluation_metrics=playbook.evaluation_metrics,
            assumptions=[
                _text(
                    state,
                    "External video generation APIs are represented as provider adapters until credentials are configured.",
                    "\u5916\u90e8\u89c6\u9891\u751f\u6210 API \u5728\u51ed\u636e\u914d\u7f6e\u524d\u4ee5 provider adapter \u5f62\u5f0f\u8868\u8fbe\u3002",
                ),
                completion,
            ],
            metadata={
                "schema_version": "solution_architecture_v1",
                "source": "solution_architect_agent",
                "playbook_id": playbook.playbook_id,
                "jd_alignment": [
                    "scenario_insight",
                    "agent_harness",
                    "skill_mcp_sandbox_memory",
                    "poc_acceptance",
                    "customer_value",
                ],
            },
        )
    return state


def _infer_industry_and_scenario(idea: str, language: str) -> tuple[str, str]:
    lower_idea = idea.lower()
    if any(term in lower_idea for term in ["ad", "brand", "commercial", "marketing"]):
        return (
            _pick(language, "Advertising", "\u5e7f\u544a\u8425\u9500"),
            _pick(language, "AI video campaign production", "AI \u89c6\u9891\u5e7f\u544a\u751f\u4ea7"),
        )
    if any(term in lower_idea for term in ["game", "character", "npc"]):
        return (
            _pick(language, "Gaming", "\u6e38\u620f"),
            _pick(language, "Game asset and trailer ideation", "\u6e38\u620f\u8d44\u4ea7\u4e0e\u9884\u544a\u7247\u521b\u610f\u751f\u4ea7"),
        )
    if any(term in lower_idea for term in ["shop", "product", "commerce", "retail"]):
        return (
            _pick(language, "Retail and E-commerce", "\u96f6\u552e\u4e0e\u7535\u5546"),
            _pick(language, "Product short-video creative operations", "\u5546\u54c1\u77ed\u89c6\u9891\u521b\u610f\u8fd0\u8425"),
        )
    return (
        _pick(language, "Media and Entertainment", "\u5f71\u89c6\u5185\u5bb9"),
        _pick(language, "AI video production planning", "AI \u89c6\u9891\u751f\u4ea7\u7b56\u5212"),
    )


def _canonical_industry(industry: str) -> str:
    mapping = {
        "\u5e7f\u544a\u8425\u9500": "Advertising",
        "\u6e38\u620f": "Gaming",
        "\u96f6\u552e\u4e0e\u7535\u5546": "Retail and E-commerce",
        "\u5f71\u89c6\u5185\u5bb9": "Media and Entertainment",
    }
    return mapping.get(industry, industry)


def _components(state: ProjectState) -> list[ArchitectureComponent]:
    return [
        ArchitectureComponent(
            name="ProjectState",
            responsibility=_text(
                state,
                "Single structured state across creative, runtime, evaluation, and exports.",
                "\u8de8\u521b\u610f\u3001\u8fd0\u884c\u65f6\u3001\u8bc4\u4f30\u548c\u5bfc\u51fa\u7684\u7edf\u4e00\u7ed3\u6784\u5316\u72b6\u6001\u3002",
            ),
            owner_agent="AgentHarnessRuntime",
            skills=[],
            guardrails=["pydantic_schema", "versioned_snapshots"],
        ),
        ArchitectureComponent(
            name="ContextBuilder",
            responsibility=_text(
                state,
                "Build scoped context packets for each agent from state, knowledge, and memory.",
                "\u57fa\u4e8e\u72b6\u6001\u3001\u77e5\u8bc6\u5e93\u548c\u8bb0\u5fc6\u4e3a\u6bcf\u4e2a Agent \u6784\u5efa\u6709\u8fb9\u754c\u7684\u4e0a\u4e0b\u6587\u5305\u3002",
            ),
            owner_agent="all_agents",
            skills=["knowledge.search"],
            guardrails=["source_count", "context_char_count"],
        ),
        ArchitectureComponent(
            name="SkillRegistry",
            responsibility=_text(
                state,
                "Register local tools and record tool-call purpose, status, latency, and permission scope.",
                "\u6ce8\u518c\u672c\u5730\u5de5\u5177\uff0c\u5e76\u8bb0\u5f55\u5de5\u5177\u8c03\u7528\u76ee\u7684\u3001\u72b6\u6001\u3001\u8017\u65f6\u548c\u6743\u9650\u8303\u56f4\u3002",
            ),
            owner_agent="AgentHarnessRuntime",
            skills=["mock_llm.complete", "export.json", "export.csv", "export.markdown"],
            guardrails=["permission_scope", "input_output_preview"],
        ),
        ArchitectureComponent(
            name="MCP / Sandbox / Memory",
            responsibility=_text(
                state,
                "Expose local resources, constrained execution, and reusable run memory as extension points.",
                "\u5c06\u672c\u5730\u8d44\u6e90\u3001\u53d7\u9650\u6267\u884c\u548c\u53ef\u590d\u7528\u8fd0\u884c\u8bb0\u5fc6\u4f5c\u4e3a\u6269\u5c55\u70b9\u66b4\u9732\u3002",
            ),
            owner_agent="AgentHarnessRuntime",
            skills=["runs.list", "runs.get_package", "sandbox.run", "memory.search"],
            guardrails=["allowlisted_commands", "dry_run_default", "local_storage"],
        ),
    ]


def _integration_points(state: ProjectState, playbook: SolutionPlaybook) -> list[IntegrationPoint]:
    integrations = [
        IntegrationPoint(
            system="FastAPI Web Demo",
            interface="/api/runs, /api/runs/{run_id}, /api/runs/{run_id}/export/{format}",
            data_contract="ProjectState JSON and exported production packages",
            status="ready",
        ),
        IntegrationPoint(
            system="Video Model Provider",
            interface="GeneratorProvider.generate(ProjectState)",
            data_contract="PromptPackage -> GeneratedResult",
            status="mocked",
        ),
        IntegrationPoint(
            system="MCP Host",
            interface="LocalMCPAdapter.call_tool/read_resource",
            data_contract="tool specs, run package resources, knowledge search results",
            status="planned",
        ),
        IntegrationPoint(
            system="Customer Asset Store",
            interface=_text(state, "file/object storage adapter", "\u6587\u4ef6/\u5bf9\u8c61\u5b58\u50a8\u9002\u914d\u5668"),
            data_contract="brand assets, references, generated artifacts",
            status="planned",
        ),
    ]
    for integration in playbook.required_integrations[:3]:
        integrations.append(
            IntegrationPoint(
                system=integration,
                interface=_text(state, "customer adapter", "\u5ba2\u6237\u4fa7\u9002\u914d\u5668"),
                data_contract=_text(state, "scenario-specific customer data", "\u573a\u666f\u5316\u5ba2\u6237\u6570\u636e"),
                status="planned",
            )
        )
    return integrations


def _safety_controls(state: ProjectState, playbook: SolutionPlaybook) -> list[str]:
    controls = [
        _text(state, "Sandbox commands are allowlisted and dry-run by default.", "Sandbox \u547d\u4ee4\u9ed8\u8ba4 dry-run\uff0c\u5e76\u901a\u8fc7\u767d\u540d\u5355\u7ea6\u675f\u3002"),
        _text(state, "Tool calls record permission scope and execution status.", "\u5de5\u5177\u8c03\u7528\u8bb0\u5f55\u6743\u9650\u8303\u56f4\u548c\u6267\u884c\u72b6\u6001\u3002"),
        _text(state, "External model providers remain mocked unless credentials are explicitly configured.", "\u5916\u90e8\u6a21\u578b provider \u5728\u672a\u663e\u5f0f\u914d\u7f6e\u51ed\u636e\u524d\u4fdd\u6301 mock/planned \u72b6\u6001\u3002"),
        _text(state, "Version snapshots preserve rollback and auditability.", "\u7248\u672c\u5feb\u7167\u652f\u6301\u56de\u6eda\u548c\u5ba1\u8ba1\u3002"),
    ]
    controls.extend(playbook.risk_controls)
    return controls


def _success_criteria(
    state: ProjectState,
    playbook: SolutionPlaybook,
) -> list[POCSuccessCriterion]:
    criteria = [
        POCSuccessCriterion(
            criterion_id="poc_latency",
            metric=_text(state, "creative package turnaround", "\u521b\u610f\u4efb\u52a1\u5305\u4ea4\u4ed8\u65f6\u95f4"),
            target=_text(state, "< 2 minutes for mock pipeline", "Mock \u94fe\u8def < 2 \u5206\u949f"),
            evaluation_method=_text(state, "trace log timestamps and export completion", "TraceLog \u65f6\u95f4\u6233\u4e0e\u5bfc\u51fa\u5b8c\u6210\u8bb0\u5f55"),
        ),
        POCSuccessCriterion(
            criterion_id="poc_observability",
            metric=_text(state, "agent harness observability", "Agent Harness \u53ef\u89c2\u6d4b\u6027"),
            target=_text(state, "context, tool calls, policies, MCP, sandbox, and memory visible per run", "\u6bcf\u6b21\u8fd0\u884c\u53ef\u89c1 context/tool/policy/MCP/sandbox/memory"),
            evaluation_method=_text(state, "Harness Inspector and exported ProjectState", "Harness Inspector \u4e0e ProjectState \u5bfc\u51fa"),
        ),
        POCSuccessCriterion(
            criterion_id="poc_quality_loop",
            metric=_text(state, "closed-loop improvement readiness", "\u95ed\u73af\u6539\u8fdb\u80fd\u529b"),
            target=_text(state, "evaluation, correction plan, diff, and verification generated", "\u80fd\u751f\u6210\u8bc4\u4f30\u3001\u4fee\u6b63\u8ba1\u5212\u3001diff \u548c\u9a8c\u8bc1\u7ed3\u679c"),
            evaluation_method=_text(state, "planning mode output", "planning \u6a21\u5f0f\u8f93\u51fa"),
        ),
    ]
    for index, metric in enumerate(playbook.evaluation_metrics[:3], start=1):
        criteria.append(
            POCSuccessCriterion(
                criterion_id=f"playbook_metric_{index}",
                metric=metric,
                target=_text(state, "measurable in evaluation report", "\u53ef\u5728\u8bc4\u4f30\u62a5\u544a\u4e2d\u91cf\u5316"),
                evaluation_method=_text(state, "scenario playbook rubric mapping", "\u573a\u666f playbook \u8bc4\u4f30\u6620\u5c04"),
            )
        )
    return criteria


def _rollout_plan(state: ProjectState) -> list[RolloutPhase]:
    return [
        RolloutPhase(
            phase="POC",
            objective=_text(state, "validate workflow, schema, exports, and demo narrative", "\u9a8c\u8bc1\u6d41\u7a0b\u3001schema\u3001\u5bfc\u51fa\u548c demo \u53d9\u4e8b"),
            exit_criteria=["mock_pipeline_passes", "web_demo_available", "json_csv_md_exports"],
        ),
        RolloutPhase(
            phase="Pilot",
            objective=_text(state, "connect one real provider and one customer asset source", "\u63a5\u5165\u4e00\u4e2a\u771f\u5b9e provider \u548c\u4e00\u4e2a\u5ba2\u6237\u7d20\u6750\u6e90"),
            exit_criteria=["provider_credentials_configured", "artifact_tracking", "manual_review_gate"],
        ),
        RolloutPhase(
            phase="Production",
            objective=_text(state, "add tenancy, governance, monitoring, and cost controls", "\u589e\u52a0\u79df\u6237\u3001\u6cbb\u7406\u3001\u76d1\u63a7\u548c\u6210\u672c\u63a7\u5236"),
            exit_criteria=["sla_defined", "cost_budgeting", "security_review"],
        ),
    ]


def _value_metrics(state: ProjectState, playbook: SolutionPlaybook) -> list[ValueMetric]:
    metrics = [
        ValueMetric(
            name=_text(state, "Speed", "\u901f\u5ea6"),
            baseline=_text(state, "manual creative brief and storyboard drafting", "\u4eba\u5de5\u64b0\u5199\u521b\u610f brief \u548c\u5206\u955c"),
            target=_text(state, "structured task package generated in one run", "\u4e00\u6b21\u8fd0\u884c\u751f\u6210\u7ed3\u6784\u5316\u4efb\u52a1\u5305"),
            business_value=_text(state, "shorter campaign iteration cycle", "\u7f29\u77ed\u8425\u9500\u5185\u5bb9\u8fed\u4ee3\u5468\u671f"),
        ),
        ValueMetric(
            name=_text(state, "Stability", "\u7a33\u5b9a\u6027"),
            baseline=_text(state, "untracked prompt experiments", "\u4e0d\u53ef\u8ffd\u6eaf\u7684 prompt \u5b9e\u9a8c"),
            target=_text(state, "state, versions, trace, and tool calls retained", "\u4fdd\u7559 state/version/trace/tool calls"),
            business_value=_text(state, "repeatable delivery and easier issue diagnosis", "\u53ef\u590d\u73b0\u4ea4\u4ed8\uff0c\u66f4\u5bb9\u6613\u5b9a\u4f4d\u95ee\u9898"),
        ),
        ValueMetric(
            name=_text(state, "Cost control", "\u6210\u672c\u63a7\u5236"),
            baseline=_text(state, "trial-and-error external generation", "\u5916\u90e8\u751f\u6210\u6a21\u578b\u53cd\u590d\u8bd5\u9519"),
            target=_text(state, "pre-flight evaluation before real model spend", "\u5728\u771f\u5b9e\u6a21\u578b\u6d88\u8017\u524d\u5148\u505a\u9884\u8bc4\u4f30"),
            business_value=_text(state, "reduce wasted generation calls", "\u51cf\u5c11\u65e0\u6548\u751f\u6210\u8c03\u7528"),
        ),
    ]
    for lever in playbook.value_levers[:2]:
        metrics.append(
            ValueMetric(
                name=lever,
                baseline=_text(state, "not tracked before POC", "POC \u524d\u672a\u7ed3\u6784\u5316\u8ffd\u8e2a"),
                target=_text(state, "tracked as a scenario value lever", "\u4f5c\u4e3a\u573a\u666f\u4ef7\u503c\u6760\u6746\u8ffd\u8e2a"),
                business_value=_text(state, "connect solution design to customer KPI", "\u5c06\u65b9\u6848\u8bbe\u8ba1\u8fde\u63a5\u5230\u5ba2\u6237 KPI"),
            )
        )
    return metrics


def _text(state: ProjectState, en: str, zh: str) -> str:
    return zh if state.language == "zh" else en


def _pick(language: str, en: str, zh: str) -> str:
    return zh if language == "zh" else en
