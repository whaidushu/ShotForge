# Volcengine JD Alignment

This document explains how ShotForge can be read for an AI Agent product solution architect role.

The project is not presented as a generic video generator. It is an AI video Agent Workbench exploration: the visible workflow is creative video production, while the reusable capability is an agent runtime with provider boundaries, evaluation loops, versioned iteration, artifact tracking, and handoff exports.

## Role Requirements Mapped To ShotForge

| JD Requirement | ShotForge Alignment |
|---|---|
| Understand industry AI scenarios and business value | Uses AI video creation as the reference scenario and includes advertising, e-commerce, and game trailer solution packages, where iteration cost, quality gates, asset handoff, and traceability are concrete workflow problems |
| Design AI Agent solutions for industry customers | Provides industry solution docs, POC strategy, model selection matrix, and an end-to-end workflow from user goal to structured package, generation provider, observation, evaluation, correction, versioning, and export |
| Connect business goals with technical constraints | Separates cheap design/evaluation loops from expensive final generation; provider strategy supports model selection, privacy, cost control, and local-first deployment constraints |
| Agent Harness engineering practice | LangGraph workflows, typed ProjectState, ContextBuilder, SkillRegistry, AgentHarnessRuntime, AgentContract, WorkflowController, TraceLog, VersionManager |
| Context Engineering | ContextBuilder injects user goal, project state, knowledge refs, and runtime memory refs with source ranking, budget, redaction, and digest |
| Tool Orchestration | SkillRegistry records tool plans, authorization decisions, schema status, fallback outcomes, status, latency, and permission scope |
| State Management | ProjectState is the single workflow contract across design, generation, observation, evaluation, correction, versioning, policies, and exports |
| MCP / Skill / Sandbox / Memory / Knowledge Base | Agent Infra Runtime exposes MCP-like tools/resources/prompts, access policy, sandbox policy records, memory governance, and local knowledge retrieval |
| Evaluation and quality system | EvaluationReport, ScoreCard, Issue, CorrectionPlan, physical/consistency/style/emotion layers, VersionDiff, ScoreDelta, RegressionCheck |
| POC and demo capability | CLI, FastAPI Web app, audit API, provider preflight, ComfyUI workflow discovery, export artifacts, run history, version chain, POC test strategy, and sales demo playbook |
| Productized value communication | SolutionArchitecture and DeliveryReadinessReport translate cost, speed, stability, traceability, provider optionality, and pilot readiness into reviewable artifacts |
| Reusable knowledge assets | Packaged industry playbooks, rubrics, correction strategies, prompt rules, solution docs, model matrix, and POC strategy are separated from code |

## Current Strength

ShotForge currently has a credible local-first engineering foundation:

- Agent workflow orchestration with LangGraph.
- Typed state and artifacts with Pydantic.
- Design, evaluation, correction, redesign, and export workflows.
- Provider abstraction for LLM/Judge, video generation, and visual observation.
- Local Ollama / vLLM / OpenAI-compatible LLM paths.
- Local ComfyUI workflow discovery and API-format workflow execution.
- Runtime evidence for context, tools, contracts, workflow decisions, policies, MCP, sandbox, and memory.
- Version snapshots, version diffs, prompt-change cards, run history, and per-iteration artifacts.
- Solution architecture and delivery readiness artifacts generated per run.
- Harness audit API and CLI audit command for reviewer-facing evidence.
- `manifest.json`, `trace.json`, `run_summary.md`, package exports, and evaluation CSV exports.
- Packaged industry playbooks and solution docs for scenario reuse.
- Internal test provider kept as a diagnostic path rather than the default user generation path.

## Remaining Production Boundaries

These are the boundaries to close before presenting it as a production customer platform:

- Dockerized deployment and simpler local bootstrap.
- Official MCP transport beyond the current local MCP-like adapter.
- Stronger sandbox isolation, such as container or remote runner execution.
- Production storage for runs, traces, memory, artifacts, and user-specific history.
- Auth, tenant isolation, quota controls, and provider credential management.
- Customer-specific playbook overlays and stronger RAG-backed knowledge retrieval.
- Cost/latency accounting for real provider benchmark runs.
- Customer discovery questionnaire, RFP template, and security review checklist.
- Production observability, background job orchestration, and retry/cancel controls for long-running generation.

## Narrative

The key narrative:

```text
ShotForge explores AI video production as an agent workflow problem.
The reusable capability is an Agent Workbench that turns vague creative intent into
traceable, evaluated, versioned, and provider-ready production packages.
```

This maps directly to the role's need to bridge customer scenarios, AI product value, and technical implementation.
