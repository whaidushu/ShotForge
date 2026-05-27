# ShotForge_BD Solution Blueprint

ShotForge_BD is framed as an industry AI Agent Harness solution for video creative workflows. The video domain is the demonstration scenario; the reusable asset is the end-to-end Agent Harness pattern.

## Business Scenario

Target users:

- Creative teams producing short-form ads or campaign videos.
- Software vendors building AI creative workflow products.
- Solution architects validating agentic workflow feasibility with customers.

Common pain points:

- Creative feedback is vague and hard to turn into engineering tasks.
- Video generation attempts are expensive when every iteration calls a large model.
- Prompt-only workflows lack traceability, versioning and quality gates.
- Different customers need different model providers, evaluation rubrics and safety policies.

## End-to-End Solution

```text
Customer Goal
  -> Context Engineering
  -> Agent Workflow
  -> Structured State
  -> Generator Provider
  -> Evaluation Harness
  -> Redesign Loop
  -> Versioned Package
  -> Export / Integration
```

## Reference Architecture

| Layer | Responsibility | Current Implementation |
| --- | --- | --- |
| Experience | Web / CLI / API demo | FastAPI, Typer, Jinja2 |
| Orchestration | Agent graph and runtime | LangGraph + AgentHarnessRuntime |
| Context | Build and trace context sources | ContextBuilder, ContextBundle |
| Agents | Design, evaluation and correction | Intent, Storyboard, Motion, Audio, Prompt, Evaluation, Correction |
| Tools | Tool registry and call trace | SkillRegistry, SkillSpec, ToolCallRecord |
| Model Providers | LLM and generation abstraction | Mock, Ollama/vLLM skeleton, GeneratorProvider catalog |
| Knowledge | Domain rules and rubrics | JSON knowledge base, evaluation rubrics, correction strategies |
| Safety | Execution and sandbox policy | ExecutionPolicy, SandboxPolicy, LocalSandbox dry-run |
| Integration | MCP extension point | MockMCPClient |
| Observability | Trace, diff, score and regression | TraceLog, VersionDiff, ScoreDelta, RegressionCheck |

## Provider Strategy

```text
POC / local demo:
  Mock LLM + Mock Generator

Iteration stage:
  Local LLM / local generator / cheap provider

Benchmark stage:
  Small batch comparison across providers

Delivery stage:
  Final converged package -> selected high-quality provider
```

The provider strategy separates creative convergence from expensive final generation. This makes cost, latency and stability easier to explain to customers.

## POC Acceptance Criteria

| Area | Acceptance signal |
| --- | --- |
| Workflow | One idea produces a complete stateful production package |
| Evaluation | System outputs scores, issues, causes and correction types |
| Redesign | At least one version diff shows what changed and why |
| Observability | Harness Inspector shows context, tools, state and policies |
| Extensibility | A new rubric dimension or provider can be added without changing core workflow |
| Safety | Runtime policy and sandbox policy are explicit in the result |

## From POC To Production

1. Replace mock LLM with selected enterprise model provider.
2. Connect customer knowledge base through RAG / MCP.
3. Replace mock generator with approved video provider.
4. Add evaluator providers for real visual/audio assessment.
5. Persist memory and traces in production stores.
6. Add deployment profiles, health checks, auth and policy enforcement.
