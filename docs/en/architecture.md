# Architecture

ShotForge is organized around one core object: a versioned video generation run.
The run starts from a user idea, passes through provider-backed generation and
evaluation, and ends as a local package with artifacts and exports.

## Layer Overview

```text
Web / CLI / API
  -> App services
  -> LangGraph workflows
  -> Agent Harness Runtime
  -> Provider adapters
  -> ProjectState + artifacts
```

ShotForge keeps the user-facing workbench and the execution runtime separated:

- **AI Video Workbench**: pages, API endpoints, run history, provider
  configuration, artifact access, progress, lifecycle status, and exports.
- **Agent Harness Runtime**: typed state, context construction, agent contracts,
  tool records, provider boundaries, trace logs, version snapshots, and policy
  records.

## Run Flow

```text
idea
-> provider profile
-> ProjectState
-> design package
-> prompt/template package
-> video provider artifact
-> frame extraction
-> visual observation
-> layered evaluation
-> correction plan
-> regenerated package/artifact
-> version diff
-> exports
```

Design-only runs stop after the prompt package and exports. Full-loop runs add
generation, observation, evaluation, readiness, and export artifacts. Planning
runs add iterative redesign and version comparison.

## Entry Points

### Web

`src/shotforge/app/web/app.py`

The Web layer renders the workbench and configuration pages. It uses the same
services as the API so behavior stays aligned across UI and automation.

Important routes:

- `/`: workflow page
- `/config`: provider configuration page
- `/demo`: seeded sample run
- `/runs`: form POST endpoint for Web run creation

### API

`src/shotforge/app/api/`

Routers are split by purpose:

- `system.py`: health and capability catalog.
- `runs.py`: run creation, package loading, artifacts, status, versions, exports.
- `providers.py`: profiles, preflight, workflow discovery, observer providers.
- `schemas.py`: request/response models used by API routes.

### CLI

`src/shotforge/app/cli/main.py`

CLI commands call the same workflow and service layer:

- `design`
- `full-loop`
- `evaluate`
- `inspect`
- `audit`
- `capabilities`
- `comfyui-workflows`
- `doctor`
- `web`

## Application Services

`src/shotforge/app/services/`

| Service | Responsibility |
| --- | --- |
| `RunService` | Creates runs, applies provider profiles, selects run mode, writes exports, records job status. |
| `ProviderService` | Lists providers, builds profiles from payloads/forms, validates generator ids, applies scoped runtime settings. |
| `ProviderProfileStore` | Reads and writes `data/provider_profiles.json`, redacting secrets for public responses. |
| `ProviderPreflightService` | Checks LLM/Judge, video provider, workflow, and visual observer readiness. |
| `ComfyUIWorkflowService` | Discovers bundled and local API-format workflows and reports callability. |
| `ArtifactService` | Maps run metadata to video, prompt, prompt JSON, and workflow artifact paths. |
| `RunStatusService` | Builds dashboard summaries, lifecycle stages, readiness scores, timelines, and handoff data. |
| `RunJobService` | Records run progress and failed/completed job state. |

These services isolate Web/API behavior from workflow implementation details.

## Core State Model

`src/shotforge/core/project_state.py`

`ProjectState` is the typed state shared by workflows, agents, providers,
evaluators, exporters, and the Web/API layer. It includes:

- identity: `project_id`, `run_id`, `version`
- user input: `user_idea`, `style`, `duration_seconds`, `target_platform`
- design: `creative_intent`, `characters`, `scenes`, `shots`, `audio_cues`
- prompts: `prompt_package`, `PromptItem`, `StructuredPromptTemplate`
- generation: `generation_results`, `GeneratedResult`, `GeneratedShotResult`
- observation: `observation_reports`, frame observations, sequence observations
- evaluation: `evaluation_reports`, `issue_history`, `verification_reports`
- iteration: `redesign_plans`, `correction_plans`, `correction_patches`,
  `version_diffs`, `score_deltas`, `regression_checks`, `convergence_steps`
- delivery: `delivery_readiness`, `exports`
- runtime evidence: trace logs, tool calls, state transitions, context snapshots,
  workflow decisions, memory records, sandbox records, access records

## Package View

`src/shotforge/core/packages.py`

The full state is useful for persistence, but UIs often need grouped sections.
`ProjectPackageView` splits state into:

- `design`
- `generation`
- `observation`
- `evaluation`
- `iteration`
- `runtime`

The API exposes this through `GET /api/runs/{run_id}/package-view`.

## Workflow Layer

`src/shotforge/workflows/`

Workflows are responsible for ordering agents and provider calls:

- design workflow: create creative intent, scenes, shots, prompts, exports.
- full-loop workflow: add generation, observation, evaluation, readiness.
- iterative redesign workflow: apply correction plans, regenerate, compare versions.
- evaluation workflow: evaluate an existing package.

## Runtime Evidence

`src/shotforge/core/harness_runtime.py`

The runtime records execution evidence during agent execution:

- context snapshots
- contract reports
- workflow decisions
- state transitions
- tool calls and orchestration records
- memory selections
- sandbox policy records
- access records

This evidence is exposed through `shotforge audit` and
`GET /api/runs/{run_id}/harness`.

## Provider Boundary

ShotForge separates provider roles:

- LLM/Judge providers decide and revise text.
- Video providers render artifacts.
- Visual observer providers inspect frames.

Provider settings are stored in provider profiles and applied through a scoped
runtime context while a run executes. This keeps provider configuration out of
the core state logic.

## Artifact Layout

By default, run data is written under:

```text
data/runs/{run_id}
```

Typical files include:

- `package.json`
- `package_view.json`
- `package.csv`
- `package.md`
- `manifest.json`
- `trace.json`
- `run_summary.md`
- `evaluation.csv`
- generated videos
- per-shot prompt text
- per-shot prompt JSON
- provider workflow payloads
- extracted frames

Version snapshots are stored separately under `data/versions`.

## Extension Points

The intended extension points are:

- new generator provider in `src/shotforge/generators/`
- new LLM/Judge provider in the LLM provider registry
- new visual observer provider in `src/shotforge/observation/providers/`
- new evaluator in `src/shotforge/evaluators/`
- new exporter in `src/shotforge/exporters/`
- new workflow node in `src/shotforge/workflows/`
- additional Web/API service in `src/shotforge/app/services/`
