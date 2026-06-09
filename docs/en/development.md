# Development

## Setup

```powershell
conda activate ShotForge
pip install -e ".[dev]"
```

## Checks

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
  app/                 CLI, Web app, shared app services
  agents/              workflow agents
  core/                state, context, trace, versioning
  evaluators/          evaluation contracts and implementations
  generators/          video generator providers
  observation/         frame extraction and visual observation
  workflows/           LangGraph workflow definitions
```

## Adding A Provider

1. Add the provider implementation under the relevant package.
2. Register it in the provider catalog or runtime service.
3. Add profile fields if users must configure it.
4. Add preflight checks for missing services, models, paths, or credentials.
5. Cover the provider contract with focused tests.

## Documentation Scope

Public docs should stay user-oriented. Internal planning, interview notes,
roadmap drafts, and design explorations belong in `_private/`, which is ignored
by git.
