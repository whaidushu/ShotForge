# Advertising AI Video Agent Solution

This solution package frames ShotForge for advertising and brand marketing teams that need faster short-video concept iteration with stronger quality control and lower model waste.

## Customer Scenario

Advertising teams often need to create multiple campaign concepts across channels, audiences, and styles. The work is slow because creative intent, storyboard, prompt engineering, visual review, and revision feedback are spread across different people and tools.

ShotForge uses AI video as the scenario and Agent Harness as the reusable solution pattern.

## Business Pain Points

| Pain Point | Business Impact | ShotForge Response |
|---|---|---|
| Creative briefs are vague | Repeated alignment meetings and unclear production tasks | Intent, storyboard, motion, audio, and prompt agents convert one idea into structured state |
| Prompt experiments are not traceable | Hard to reproduce good outputs or diagnose bad ones | ProjectState, trace log, version snapshots, prompt diffs |
| Video model calls are expensive | Wasted generations before the concept is stable | Cheap design/evaluation loop before real provider execution |
| Review feedback is subjective | Corrections are broad and inconsistent | Evaluation reports, issue taxonomy, correction routing |
| Model/provider lock-in | Risk when cost, latency, or quality changes | Provider profiles for mock, local, OpenAI-compatible, and ComfyUI paths |

## Reference Agent Workflow

```text
Campaign goal
-> Intent Agent
-> Storyboard Agent
-> Motion Agent
-> Audio Cue Agent
-> Prompt Adapter Agent
-> Video Provider
-> Frame Observation
-> Layered Evaluation
-> Correction / Redesign
-> Client-ready package
```

## POC Scope

| Area | POC Boundary |
|---|---|
| Input | One campaign idea, audience, style, duration, target platform |
| Output | JSON package, storyboard CSV, Markdown brief, trace, run summary |
| Provider | Mock generator for deterministic demo, ComfyUI for local video generation |
| Evaluation | Physical target presence, prompt alignment, storyboard/prompt quality |
| Human Review | Review readiness report and prompt/version diffs |
| Integration | Export package and MCP-like run resources |

## Success Criteria

| Metric | Target | Evidence |
|---|---|---|
| Creative package speed | One idea to package in minutes | Run summary and trace timestamps |
| Prompt traceability | Every prompt tied to shot and version | ProjectState, prompt package, version diff |
| Quality gate coverage | At least physical target and prompt/story checks | Evaluation report |
| Provider readiness | Configured profile and preflight result | Provider service metadata |
| Handoff readiness | Clear next actions and risk register | DeliveryReadinessReport |

## Customer Value

- **Cost**: reduce wasted video generations by evaluating before final model spend.
- **Speed**: compress creative brief, storyboard, prompt, and review handoff into one workflow.
- **Stability**: keep state, versions, policies, and trace logs for reproducible delivery.
- **Control**: expose context, tools, model providers, evaluation, and correction decisions.

## Production Path

1. Configure one approved LLM/Judge provider.
2. Connect campaign knowledge and brand rules through knowledge assets or MCP.
3. Configure video generation provider and preflight checks.
4. Add brand-specific evaluation dimensions.
5. Add approval gates before expensive generation.
6. Persist runs, artifacts, memory, and audit evidence in production storage.
