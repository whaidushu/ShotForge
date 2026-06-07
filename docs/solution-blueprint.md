# Solution Blueprint

ShotForge is a reference AI Agent workbench for video creative workflows.

The reference domain is short-form video advertising and creative production. The reusable asset is the end-to-end Agent Harness pattern with evaluation, versioned iteration, artifact tracking, and handoff exports.

## Customer Scenario

Target customers:

- Advertising and creative teams.
- Software companies building AI creative workflow products.
- Video production teams evaluating agentic AI workflows.
- Solution architects validating whether an AI Agent system can move beyond a prompt demo.

Typical pain points:

- Creative feedback is vague and difficult to convert into engineering tasks.
- Prompt-only workflows lack traceability and quality gates.
- Repeated calls to expensive video models increase cost.
- Different customers require different model providers, rubrics, safety policies, and integration paths.

## Solution Flow

```text
Business Goal
  -> Context Engineering
  -> Agent Workflow
  -> Structured ProjectState
  -> Solution Architecture
  -> Delivery Readiness Gates
  -> Generator Provider / ComfyUI
  -> Visual Observation
  -> Evaluation Harness
  -> Correction / Redesign Loop
  -> Version Diff / Run History
  -> Versioned Run Package
  -> Export / Integration
```

## Reference Architecture

| Layer | Responsibility | ShotForge Implementation |
|---|---|---|
| Experience | Local Web / CLI / API demo | FastAPI, Typer, Jinja2 |
| Orchestration | Agent graph and runtime | LangGraph + AgentHarnessRuntime |
| Context | Build and trace context sources | ContextBuilder, KnowledgeBase, Memory refs |
| Agents | Design, evaluation, correction, export | Intent, Storyboard, Motion, Audio, Prompt, Evaluation, Correction |
| Tools | Tool registry and call trace | SkillRegistry, ToolCallRecord |
| Model Providers | LLM, video, and visual-observer abstraction | Mock diagnostics, Ollama, vLLM, OpenAI-compatible LLM, ComfyUI, VLM observer providers |
| Knowledge | Domain rules and rubrics | JSON knowledge assets and evaluation rubrics |
| Solution Assets | Industry scenario patterns and POC path | SolutionPlaybookStore, SolutionArchitecture |
| Safety | Runtime and sandbox policy | ExecutionPolicy, SandboxPolicy, LocalSandboxRunner |
| Integration | Agent tool/resource boundary | LocalMCPAdapter |
| Observability | Run trace, artifacts, and version evidence | TraceLog, VersionManager, VersionDiff, ScoreDelta, RegressionCheck, run history |
| Readiness | Handoff gates and pilot next actions | DeliveryReadinessReport |

## Provider Strategy

```text
Diagnostic stage:
  Internal test provider / prompt-proxy observer

Iteration stage:
  Local or low-cost LLM/VLM provider + ComfyUI or selected generator

Benchmark stage:
  Small-batch comparison across candidate providers

Delivery stage:
  Final converged package -> selected production provider
```

This separates cheap planning/evaluation cycles from expensive final generation, making cost, quality, and version history easier to explain.

## POC Acceptance Criteria

| Area | Acceptance Signal |
|---|---|
| Workflow | One idea produces a complete stateful production package |
| Evaluation | System outputs scores, issues, suspected causes, and correction types |
| Redesign | Version diff shows what changed and why |
| Observability | Runtime evidence shows context, tools, policies, MCP, sandbox, memory, traces, and artifacts |
| Solution Design | SolutionArchitecture shows industry, scenario, model strategy, integrations, playbook references, and POC success criteria |
| Readiness | DeliveryReadinessReport shows gates, handoff deliverables, next actions, and risks |
| Extensibility | A rubric, provider, or tool can be added without rewriting the workflow |
| Delivery | Exports are available for human review and system integration |

## Industry Solution Packages

ShotForge now includes reusable solution packages for customer-facing discussions:

- [Advertising AI Video Agent Solution](solutions/advertising-agent-solution.md)
- [E-commerce Product Video Agent Solution](solutions/ecommerce-video-agent-solution.md)
- [Game Trailer And Character Video Agent Solution](solutions/game-trailer-agent-solution.md)

These packages translate the same Agent Harness into different customer scenarios, pain points, POC boundaries, success criteria, and production paths.

## Supporting Solution Assets

- [POC Test Strategy](poc-test-strategy.md)
- [Model Selection Matrix](model-selection-matrix.md)
- [Sales Demo Playbook](sales-demo-playbook.md)
- [Knowledge Assets](knowledge-assets.md)

## From POC To Production

1. Package deployment with simpler local bootstrap or Docker.
2. Connect customer knowledge through RAG, MCP, or customer-specific playbook overlays.
3. Replace local storage with production stores for runs, memory, traces, and artifacts.
4. Add auth, tenancy, quota controls, and provider credential management.
5. Add production observability, background jobs, retry/cancel controls, and policy enforcement.
6. Harden MCP transport and sandbox execution for customer environments.

## Customer Value

ShotForge should be explained in business terms:

- **Cost**: converge cheaply before calling expensive generation providers.
- **Speed**: automate storyboard, prompt, evaluation, correction, and export.
- **Stability**: use typed state, trace logs, version snapshots, and policy boundaries.
- **Control**: make context, tools, models, and quality gates visible.
