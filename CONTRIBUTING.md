# Contributing

ShotForge is a local-first AI video workflow platform for creative planning,
generation, evaluation, iteration, and export.

## Development Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Checks

Run these before opening a PR:

```bash
python -m ruff check src tests
python -m pytest
```

## Contribution Scope

Good contributions include:

- Agent Harness runtime improvements
- ContextBuilder, SkillRegistry, MCP, Sandbox, Memory, or Knowledge Base extensions
- generator provider adapters
- evaluation rubrics and correction agents
- export and handoff improvements
- public docs that explain solution architecture, provider setup, or delivery workflows

Avoid committing:

- local `data/` run outputs
- credentials or `.env`
- private planning notes under `_private/`

## Design Principles

- Keep the local development path runnable without paid model calls.
- Prefer typed state and explicit artifacts over hidden side effects.
- Make agent execution inspectable through trace, audit API, Web, and CLI.
- Keep public docs clear about implemented behavior, test providers, and planned adapters.
