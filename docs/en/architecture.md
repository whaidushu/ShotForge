# Architecture

ShotForge has two connected layers:

- **AI Video Workbench**: the Web/API/CLI surface for creating runs, configuring
  providers, inspecting prompts and artifacts, evaluating outputs, comparing
  versions, and exporting deliverables.
- **Agent Harness Runtime**: the inspectable execution layer for typed state,
  context construction, agent contracts, tool calls, provider boundaries,
  evaluation, traces, and version snapshots.

## Run Flow

```text
idea
-> provider profile
-> ProjectState
-> design package
-> prompt/template package
-> video provider artifact
-> frame extraction and visual observation
-> layered evaluation
-> correction plan
-> regenerated package/artifact
-> version diff
-> export
```

## Main Modules

```text
src/shotforge/
  app/          CLI and FastAPI Web entrypoints
  agents/       design, evaluation, correction, structuring, export agents
  core/         ProjectState, context, tracing, versioning, rubrics
  evaluators/   static and provider-backed evaluators
  generators/   test and real video generator providers
  observation/  frame extraction and visual observation
  workflows/    LangGraph workflow definitions
```

## State And Artifacts

`ProjectState` is the typed object shared across workflows. Run artifacts are
stored under `data/runs/{run_id}` so prompts, videos, observations, evaluations,
versions, traces, and exports can be inspected together.

## Extension Boundaries

The current extension points are:

- LLM/Judge providers
- Video generator providers
- Visual observer providers
- evaluation rubrics
- correction agents
- exporters
- workflow nodes
