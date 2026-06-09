# Development

This guide covers local development, tests, and extension patterns.

## Setup

```powershell
conda activate ShotForge
pip install -e ".[dev]"
```

## Checks

Run the standard checks:

```powershell
ruff check src tests
pytest -q
```

Run focused tests while working:

```powershell
pytest tests/test_web.py tests/test_cli.py -q
```

## Project Layout

```text
src/shotforge/
  app/
    api/             FastAPI routers and API schemas
    cli/             Typer CLI commands
    services/        shared Web/API application services
    web/             FastAPI pages, templates, static UI assets
  agents/            workflow agents
  core/              state, packages, trace, versioning, runtime evidence
  evaluators/        evaluation contracts and implementations
  exporters/         JSON, CSV, Markdown, manifest, trace exporters
  generators/        video generator provider contracts and adapters
  i18n/              English and Chinese UI/output strings
  knowledge/         rubric and prompt-support assets
  observation/       frame extraction, frame observers, sequence observation
  workflows/         LangGraph workflow definitions
```

## Adding An API Endpoint

1. Add request/response models in `src/shotforge/app/api/schemas.py` when the
   endpoint accepts structured input.
2. Add the route in the relevant router under `src/shotforge/app/api/`.
3. Keep business logic in `src/shotforge/app/services/` instead of the route
   function.
4. Add tests for success and failure cases.
5. Update [API Reference](api-reference.md).

## Adding A Generator Provider

1. Implement the `GeneratorProvider` protocol.
2. Return a `GeneratedResult` with shot metadata that points to local artifacts.
3. Register the provider in the generator catalog.
4. Add provider profile fields if the provider needs configuration.
5. Add preflight checks.
6. Add tests for `supports_real_generation`, `capabilities`, and failure modes.

## Adding A Visual Observer

1. Add a descriptor in `observation/providers/registry.py`.
2. Implement a frame observer or VLM call wrapper.
3. Return structured observations with detected elements and summaries.
4. Add configuration fields only when the provider needs model/base URL/key.
5. Add preflight checks and tests.

## Adding An Evaluator

1. Implement `EvaluatorProvider`.
2. Return `EvaluationSignal` records with scores and evidence.
3. Register the evaluator in `EvaluatorRegistry.defaults()`.
4. Add rubric dimensions or signal keys when needed.
5. Add tests for expected issue creation and score behavior.

## Working With State

Prefer adding typed fields to `ProjectState` or package models when data is part
of the run contract. Use `metadata` for provider-specific or temporary details.

State-changing code should:

- update `ProjectState`
- call `state.touch()` when appropriate
- add trace or runtime records when the step matters for inspection
- export updated packages after workflow completion

## UI Assets

Static UI assets live under `src/shotforge/app/web/static/`:

- `design-system.css`: tokens and shared layout primitives
- `shotforge-ui.js`: reusable browser behavior
- `README.md`: static asset organization notes

Keep visual components reusable and keep provider/workflow logic in services.

## Documentation Scope

Public docs should explain how to install, configure, use, inspect, and extend
the project. Update docs in the same change when behavior, endpoints, or
configuration fields change.
