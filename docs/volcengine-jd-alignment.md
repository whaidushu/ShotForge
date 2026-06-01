# Volcengine JD Alignment

This document explains how ShotForge is positioned for an AI Agent product solution architect role.

The project is not presented as a generic video generator. It is presented as a reusable Agent Harness solution, with AI video creative production used as the industry scenario.

## Role Requirements Mapped To ShotForge

| JD Requirement | ShotForge Evidence |
|---|---|
| Understand industry AI scenarios and business value | Uses AI video creation as the reference scenario and includes advertising, e-commerce, and game trailer solution packages |
| Design AI Agent solutions for industry customers | Provides industry solution docs, POC strategy, model selection matrix, and an end-to-end workflow from user goal to evaluated export |
| Connect business goals with technical constraints | Separates cheap design/evaluation loops from expensive final generation; provider strategy supports model selection, privacy, and cost control |
| Agent Harness engineering practice | LangGraph workflows, typed ProjectState, ContextBuilder, SkillRegistry, AgentHarnessRuntime, AgentContract, WorkflowController, TraceLog, VersionManager |
| Context Engineering | ContextBuilder injects user goal, project state, knowledge refs, and runtime memory refs with source ranking, budget, redaction, and digest |
| Tool Orchestration | SkillRegistry records tool plans, authorization decisions, schema status, fallback outcomes, status, latency, and permission scope |
| State Management | ProjectState is the single workflow contract across design, generation, observation, evaluation, correction, versioning, policies, and exports |
| MCP / Skill / Sandbox / Memory / Knowledge Base | Agent Infra Runtime exposes MCP-like tools/resources/prompts, access policy, sandbox policy records, memory governance, and local knowledge retrieval |
| Evaluation and quality system | EvaluationReport, ScoreCard, Issue, CorrectionPlan, VersionDiff, ScoreDelta, RegressionCheck |
| POC and demo capability | CLI, FastAPI Web Demo, audit API, export artifacts, run history, POC test strategy, and sales demo playbook |
| Productized value communication | SolutionArchitecture and DeliveryReadinessReport translate cost, speed, stability, traceability, provider optionality, and pilot readiness into reviewable artifacts |
| Reusable knowledge assets | Packaged industry playbooks, rubrics, correction strategies, prompt rules, solution docs, model matrix, and POC strategy are separated from code |

## Current Strength

ShotForge already demonstrates a credible engineering foundation:

- Agent workflow orchestration with LangGraph.
- Typed state and artifacts with Pydantic.
- Design, evaluation, correction, redesign, and export workflows.
- Provider abstraction for LLM and video generation.
- Runtime evidence for context, tools, contracts, workflow decisions, policies, MCP, sandbox, and memory.
- Solution architecture and delivery readiness artifacts generated per run.
- Harness audit API and CLI audit command for reviewer-facing evidence.
- Packaged industry playbooks and solution docs for scenario reuse.
- Local-first POC execution without requiring expensive model calls.

## Current Gaps

These are the gaps to close before presenting it as a stronger solution architect project:

- Add official MCP transport instead of the current local adapter.
- Replace local sandbox policy gates with container or remote execution isolation for production use.
- Add customer-specific playbook overlays and RAG-backed knowledge retrieval.
- Add cost/latency accounting for real provider benchmark runs.
- Add customer discovery questionnaire, RFP template, and security review checklist.

## Narrative For Interview

The key interview narrative:

```text
ShotForge treats video creative production as a customer scenario.
The reusable capability is an Agent Harness that turns vague creative intent into
traceable, evaluated, versioned, and provider-ready production packages.
```

This maps directly to the role's need to bridge customer scenarios, AI product value, and technical implementation.
