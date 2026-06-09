# Agent Harness Layer

The Agent Harness layer is the inspectable runtime underneath ShotForge. It is
responsible for AI system design and software engineering depth: typed state,
context construction, agent contracts, tool orchestration, memory, MCP-style
access, sandbox policy, evaluation, traceability, and versioned iteration.

It should stay clean, testable, modular, and explainable.

## Positioning

ShotForge is an AI video workbench built on top of this runtime layer.

The runtime converts a one-line idea into a structured production package
through explicit state, agent nodes, evaluation signals, correction plans,
version snapshots, and exports.

The main value is not "one prompt generates a video". The main value is:

```text
structured state + agent orchestration + evaluation loop + extensible provider boundary
```

## What This Layer Should Make Inspectable

- Clear domain modeling with Pydantic.
- Deterministic workflow orchestration with LangGraph.
- Traceable agent execution.
- Context engineering through a dedicated ContextBuilder.
- Tool orchestration through registries.
- Local file storage with version snapshots.
- Evaluation and correction as first-class workflow steps.
- Clean extension points for generators, evaluators, MCP, sandboxing, and external APIs.
- Tests around pipeline behavior, API behavior, i18n, generators, and evaluators.
- Runtime evidence for context, tool calls, MCP tools, sandbox policy, and memory hits.
- Versioned iteration through snapshots, diffs, run history, and export artifacts.

## Core Modules

```text
src/shotforge/core/
  project_state.py        State model and production package schema
  context_builder.py      Agent context construction
  knowledge_base.py       Lightweight knowledge retrieval
  rubrics.py              Evaluation rubric loading
  trace_log.py            Execution trace events
  version_manager.py      Snapshot persistence
  version_diff.py         Version comparison
  convergence_engine.py   Iterative refinement stop logic
  regression_check.py     Regression detection
  harness_runtime.py      Runtime snapshots for context, tools, MCP, sandbox, memory
```

```text
src/shotforge/workflows/
  design_workflow.py
  evaluation_workflow.py
  full_loop_workflow.py
  redesign_workflow.py
  redesign_planning_workflow.py
  iterative_redesign_workflow.py
```

```text
src/shotforge/agents/
  design/
  evaluation/
  correction/
  structuring/
  export/
```

## Runtime Boundaries

The runtime layer should not become a heavy product app. It should expose
capabilities that the workbench can use without embedding UI assumptions into
the core workflow.

Good additions:

- More robust state schemas.
- Better trace and version diff APIs.
- More evaluator plugins.
- Better correction routing.
- Provider abstraction improvements.
- MCP and sandbox interfaces.
- More tests and fixtures.

Risky additions:

- Heavy front-end logic inside the core workflow.
- Product-specific UI assumptions leaking into state models.
- Direct dependency on one commercial video model.
- Unstructured prompt strings becoming the only source of truth.

## Reviewer Signals

A reviewer should be able to see:

- The system is not a script collection.
- State transitions are explicit.
- The workflow can be tested without real model calls.
- Provider boundaries are designed before external integrations are added.
- Evaluation/refinement is part of the architecture, not an afterthought.

## Next Runtime Milestones

1. Strengthen typed contracts between agents.
2. Add a trace viewer API and compact trace summary.
3. Add fixture-based tests for version diff and regression checks.
4. Extend the MCP-like adapter toward official transport when needed.
5. Harden sandbox execution beyond local policy checks when needed.
