# POC Test Strategy

This document defines how ShotForge should be evaluated as an AI Agent solution POC, not only as a video-generation demo.

## POC Goal

Prove that a vague video creative goal can be converted into a structured, traceable, evaluated, and provider-ready production package through an Agent Harness.

The POC should answer three questions:

1. Can the workflow create a usable production package?
2. Can the system explain how it reached that package?
3. Can quality issues be evaluated and routed into targeted redesign?

## Test Phases

| Phase | Purpose | Required Evidence |
|---|---|---|
| Environment Preflight | Verify local services and provider settings | Doctor output, provider profile, preflight result |
| Design Run | Generate structured plan from idea | ProjectState, storyboard CSV, prompt package |
| Harness Audit | Verify runtime governance | Context, tools, contracts, workflow decisions, memory, MCP, sandbox |
| Generation Run | Produce mock or real video artifacts | GeneratedResult, artifact paths, provider metadata |
| Observation | Inspect generated frames or proxy output | ObservationReport and frame observations |
| Evaluation | Convert output quality into issue records | EvaluationReport, score card, issue taxonomy |
| Redesign | Apply targeted corrections | CorrectionPlan, CorrectionPatch, VersionDiff |
| Handoff | Export reviewable package | JSON, CSV, Markdown, manifest, trace, run summary |

## Acceptance Gates

| Gate | Pass Condition | Failure Action |
|---|---|---|
| State completeness | Intent, shots, prompts, readiness, exports exist | Re-run design agents or block handoff |
| Contract validity | Agent pre/postconditions pass | Route to repair or review |
| Context auditability | Each agent has context digest and source metadata | Fix ContextBuilder policy |
| Tool governance | Tool calls have permission scope, purpose, schema/fallback status | Review SkillRegistry policy |
| Memory governance | Selection or promotion decisions are recorded | Seed memory or adjust MemoryGovernancePolicy |
| MCP boundary | Tools/resources/prompts are listed and access is recorded | Adjust MCPAccessPolicy |
| Sandbox boundary | Policy snapshot exists, unsafe commands denied | Tighten SandboxPolicy |
| Evaluation coverage | Physical/prompt/story quality dimensions produce scores | Add rubric or observer provider |
| Export readiness | Required package artifacts exist | Re-run export agent |

## Test Cases

| Case | Input | Expected Outcome |
|---|---|---|
| Advertising concept | Short brand campaign idea | Complete creative package and readiness report |
| E-commerce product video | Product selling-point idea | Product facts and visible elements appear in prompt/evaluation |
| Game character beat | Character + action + location | Identity/action constraints are preserved through redesign |
| Provider unavailable | ComfyUI or LLM endpoint disabled | Preflight reports failure without corrupting run state |
| Policy denial | Unsafe sandbox command or denied MCP resource | Structured denial record and reviewable reason |

## Metrics

| Metric | Meaning | Source |
|---|---|---|
| Time to package | Speed from idea to structured deliverable | TraceLog and run summary |
| Prompt coverage | Whether required visible elements enter prompt package | Physical targets and prompt package |
| Evaluation score | Quality signal across rubric dimensions | EvaluationReport |
| Correction precision | Whether redesign touches targeted fields | CorrectionPatch and VersionDiff |
| Provider readiness | Whether selected provider can run | Preflight and provider metadata |
| Audit completeness | Whether harness evidence exists | Harness audit |

## Production Exit Criteria

Before treating a POC as production-ready:

1. Replace mock providers with approved provider profiles.
2. Add customer-specific knowledge and policy overlays.
3. Persist runs, memory, artifacts, and traces in production storage.
4. Add auth, tenant boundary, and approval gates.
5. Add official MCP transport if external hosts need integration.
6. Replace local sandbox policy with container or remote execution isolation where needed.
