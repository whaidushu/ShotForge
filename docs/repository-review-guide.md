# Repository Review Guide

This document is for a reviewer who opens the repository and has limited time.

## 30-Second Read

ShotForge is an AI video Agent Workbench exploration with two tracks:

- Engineering Harness: agent workflow architecture, typed state, traceability, versioning, evaluation, and provider extensibility.
- Product Studio: the same core surfaced as a short-video creation workflow with provider configuration, run history, artifacts, prompt changes, and exports.

The current default branch keeps the Engineering Harness and Product Studio connected while preserving their boundaries.

## What To Look At First

1. `README.md`: project positioning and quick start.
2. `docs/project-spine-and-demo-path.md`: one-page project framing and review path.
3. `docs/architecture-overview.md`: runtime, provider, API, and deliverable map.
4. `docs/product-track.md`: product workflow and roadmap.
5. `src/shotforge/core/project_state.py`: typed project state.
6. `src/shotforge/workflows/`: LangGraph workflow definitions.
7. `tests/`: behavior coverage.

## Why This Project Exists

AI video generation is not only a model-call problem. For complex creative output, the harder workflow problem is:

```text
plan -> generate -> observe -> evaluate -> correct -> version -> converge -> export
```

ShotForge treats that loop as both the product surface and the engineering surface.

## Engineering Highlights

- Pydantic state model across the workflow.
- LangGraph orchestration.
- Provider surfaces for LLM/Judge, video generation, visual observation, and diagnostic test chains.
- Evaluation rubrics and correction planning.
- Version snapshots, version diffs, prompt-change cards, and run history.
- Trace logs and harness audit APIs.
- Exporters for JSON, CSV, Markdown, manifest, trace, run summary, and evaluation reports.
- Chinese/English output support.
- Extension boundaries for MCP, sandboxing, memory, knowledge assets, and video model APIs.

## Product Highlights

- Web app for one-idea video generation workflows.
- Provider profile configuration and preflight checks.
- ComfyUI workflow discovery and artifact links.
- Storyboard and prompt package output.
- Evaluation and refinement surface.
- Version chain and prompt diff view.
- Exportable production package.

## How To Run

```powershell
pip install -e ".[dev]"
shotforge design "一只赛博猫在雨夜上海屋顶追逐发光无人机"
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
uvicorn shotforge.app.web.app:app --reload
```

## What To Inspect

- How vague intent becomes structured state.
- How providers are configured and checked before generation.
- How generated prompts, videos, observations, and evaluations are connected.
- How version diffs explain what changed between iterations.
- How artifacts and exports support handoff rather than only screen output.
