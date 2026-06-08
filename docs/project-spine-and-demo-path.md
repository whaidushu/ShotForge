# Project Spine And Demo Path

This document is the short version of how ShotForge should be understood and
reviewed.

## One Sentence

ShotForge is a local-first AI video workbench that connects provider
configuration, generation, visual observation, layered evaluation, correction,
versioning, and export into one inspectable run workflow.

## Architecture Spine

```text
User idea
-> Provider profile
-> ProjectState
-> Design package
-> Prompt/template package
-> Video provider artifact
-> Frame extraction and visual observation
-> Layered evaluation
-> Correction plan
-> Regenerated package/artifact
-> Version diff and run history
-> Export and handoff files
```

The core product object is the run:

- creative goal and language/style settings
- selected provider profile
- generated prompt/template package
- video, workflow, frame, and export artifacts
- physical target contract and observation summary
- evaluation reports and correction plans
- version snapshots and diffs
- runtime audit and readiness metadata

## Current Runtime Modules

- `ProjectState`: typed state shared across agents, providers, evaluation,
  exports, and versioning.
- `RunService`: Web/API run creation, provider profile application, and export
  orchestration.
- `ProviderService` and `ProviderRuntimeService`: provider catalogs, profiles,
  validation, and runtime settings.
- `ComfyUIWorkflowService`: bundled and local API-format workflow discovery.
- `ArtifactService`: prompt, workflow, video, and frame artifact lookup.
- `VideoObservationService`: frame extraction and observer execution.
- `EvaluationAgent` and evaluator registry: physical, consistency, static, and
  LLM/Judge evaluation signals.
- `VersionManager` and `VersionDiffBuilder`: snapshots, diffs, and run history.
- `AgentHarnessRuntime`: context snapshots, tool records, policies, sandbox,
  memory, and runtime audit evidence.

## Primary Demo Path

Use the Web app for the clearest current flow:

```powershell
shotforge web --reload
```

Open:

```text
http://127.0.0.1:8000
```

Recommended review order:

1. Open Configuration and select/save a provider profile.
2. Run preflight and confirm provider readiness.
3. Return to Workflow and enter an idea.
4. Run design or full-loop mode.
5. Inspect storyboard, prompt package, and generated artifacts.
6. Review physical targets, observations, evaluation issues, and correction plan.
7. Compare version changes and export the run package.

The CLI path is still useful for fast verification:

```powershell
shotforge design "A cyber cat chases a glowing drone across rainy Shanghai rooftops" --language en
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
shotforge audit data/runs/{run_id}/package.json
```

## API Review Path

Useful endpoints:

```text
GET /api/health
GET /api/capabilities
POST /api/runs
GET /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/status
GET /api/runs/{run_id}/workbench
GET /api/runs/{run_id}/generation-artifacts
GET /api/runs/{run_id}/harness
GET /api/runs/{run_id}/readiness
GET /api/runs/{run_id}/versions
GET /api/runs/{run_id}/export/{format}
GET /api/provider-profiles
POST /api/provider-profiles
GET /api/observer-providers
POST /api/preflight
GET /api/comfyui/workflows
```

`GET /api/runs/{run_id}/workbench` is the best product-level inspection path.
`GET /api/runs/{run_id}/harness` is the best runtime-level inspection path.

## Current Boundary

ShotForge is still local-first. It currently has:

- Web, CLI, and API entrypoints.
- Provider profiles for LLM/Judge, video generation, and visual observation.
- Real ComfyUI integration when local services and API-format workflows exist.
- Local test providers for deterministic development and CI.
- Layered evaluation with physical target extraction and visual observation.
- Versioned iteration artifacts and export formats.
- Runtime audit surfaces for context, tools, policies, sandbox, and memory.

Production hardening remains separate from the current code path: deployment
packaging, auth, tenant isolation, durable storage, observability, quotas, and
stronger sandbox isolation should be added deliberately rather than implied by
the local workbench.
