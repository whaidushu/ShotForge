# Volcengine JD Alignment

This document explains how ShotForge is positioned for an AI Agent product solution architect role.

The project is not presented as a generic video generator. It is presented as a reusable Agent Harness solution, with AI video creative production used as the industry scenario.

## Role Requirements Mapped To ShotForge

| JD Requirement | ShotForge Evidence |
|---|---|
| Understand industry AI scenarios and business value | Uses advertising / video creative production as the reference scenario, where iteration cost, quality gates, and traceability are concrete business problems |
| Design AI Agent solutions for industry customers | Provides an end-to-end workflow from user goal to structured package, generation provider, evaluation, correction, versioning, and export |
| Connect business goals with technical constraints | Separates cheap design/evaluation loops from expensive final generation; provider strategy supports model selection and cost control |
| Agent Harness engineering practice | LangGraph workflows, typed ProjectState, ContextBuilder, SkillRegistry, AgentHarnessRuntime, TraceLog, VersionManager |
| Context Engineering | ContextBuilder injects user goal, project state, knowledge refs, and runtime memory refs into agent execution |
| Tool Orchestration | SkillRegistry records tool calls, permission scopes, status, latency, and previews |
| State Management | ProjectState is the single workflow contract across design, generation, evaluation, correction, versioning, and exports |
| MCP / Skill / Sandbox / Memory / Knowledge Base | Agent Infra Runtime v0 exposes MCP-like tools/resources, sandbox policy, JSONL memory, and local knowledge retrieval |
| Evaluation and quality system | EvaluationReport, ScoreCard, Issue, CorrectionPlan, VersionDiff, ScoreDelta, RegressionCheck |
| POC and demo capability | CLI, FastAPI Web Demo, audit API, export artifacts, run history, and demo script |
| Productized value communication | SolutionArchitecture and DeliveryReadinessReport translate cost, speed, stability, traceability, provider optionality, and pilot readiness into reviewable artifacts |
| Reusable knowledge assets | Packaged industry playbooks, rubrics, correction strategies, prompt rules, and solution blueprint are separated from code |

## Current Strength

ShotForge already demonstrates a credible engineering foundation:

- Agent workflow orchestration with LangGraph.
- Typed state and artifacts with Pydantic.
- Design, evaluation, correction, redesign, and export workflows.
- Provider abstraction for LLM and video generation.
- Runtime evidence for context, tools, policies, MCP, sandbox, and memory.
- Solution architecture and delivery readiness artifacts generated per run.
- Harness audit API and CLI audit command for reviewer-facing evidence.
- Packaged industry playbooks for scenario reuse.
- Local-first POC execution without requiring expensive model calls.

## Current Gaps

These are the gaps to close before presenting it as a stronger solution architect project:

- Add `.env.example` and OpenAI-compatible real LLM provider configuration.
- Export `manifest.json`, `trace.json`, and `run_summary.md` for each run.
- Add Docker / deployment notes for POC delivery.
- Add official MCP transport and a stronger sandbox isolation boundary.
- Add customer-specific playbook overlays and RAG-backed knowledge retrieval.

## Narrative For Interview

The key interview narrative:

```text
ShotForge treats video creative production as a customer scenario.
The reusable capability is an Agent Harness that turns vague creative intent into
traceable, evaluated, versioned, and provider-ready production packages.
```

This maps directly to the role's need to bridge customer scenarios, AI product value, and technical implementation.
