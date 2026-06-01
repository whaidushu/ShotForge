# Solution Blueprint

ShotForge is a reference AI Agent solution for video creative workflows.

The demonstration domain is short-form video advertising and creative production. The reusable asset is the end-to-end Agent Harness pattern.

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
  -> Mock or Real Generator Provider
  -> Evaluation Harness
  -> Correction / Redesign Loop
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
| Model Providers | LLM and generation abstraction | Mock, Ollama/vLLM skeleton, GeneratorProvider catalog |
| Knowledge | Domain rules and rubrics | JSON knowledge assets and evaluation rubrics |
| Solution Assets | Industry scenario patterns and POC path | SolutionPlaybookStore, SolutionArchitecture |
| Safety | Runtime and sandbox policy | ExecutionPolicy, SandboxPolicy, LocalSandboxRunner |
| Integration | Agent tool/resource boundary | LocalMCPAdapter |
| Observability | Run trace and version evidence | TraceLog, VersionDiff, ScoreDelta, RegressionCheck |
| Readiness | Handoff gates and pilot next actions | DeliveryReadinessReport |

## Provider Strategy

```text
POC stage:
  Mock LLM + Mock Generator

Iteration stage:
  Local or low-cost model provider

Benchmark stage:
  Small-batch comparison across candidate providers

Delivery stage:
  Final converged package -> selected production provider
```

This separates creative convergence from expensive final generation, making cost and quality easier to explain.

## POC Acceptance Criteria

| Area | Acceptance Signal |
|---|---|
| Workflow | One idea produces a complete stateful production package |
| Evaluation | System outputs scores, issues, suspected causes, and correction types |
| Redesign | Version diff shows what changed and why |
| Observability | Runtime evidence shows context, tools, policies, MCP, sandbox, and memory |
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

1. Replace mock LLM with the selected enterprise LLM provider.
2. Connect customer knowledge through RAG or MCP.
3. Replace mock generator with approved video/image provider.
4. Add real visual/audio evaluators.
5. Persist memory, traces, and runs in production stores.
6. Add auth, deployment profiles, health checks, and policy enforcement.

## Customer Value

ShotForge should be explained in business terms:

- **Cost**: converge cheaply before calling expensive generation providers.
- **Speed**: automate storyboard, prompt, evaluation, correction, and export.
- **Stability**: use typed state, trace logs, version snapshots, and policy boundaries.
- **Control**: make context, tools, models, and quality gates visible.
