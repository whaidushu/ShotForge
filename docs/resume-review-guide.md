# Resume Review Guide

This document is for a reviewer who opens the repository from a resume link and has limited time.

## 30-Second Read

ShotForge is an AI video creative agent project with two tracks:

- Engineering Harness: demonstrates agent workflow architecture, typed state, traceability, versioning, evaluation, and provider extensibility.
- Product Studio: evolves the same core into a complete short-video creation workflow.

The current default branch emphasizes the Engineering Harness while keeping Product Studio milestones explicit.

## What To Look At First

1. `README.md`: project positioning and quick start.
2. `docs/engineering-track.md`: engineering architecture and boundaries.
3. `docs/product-track.md`: product workflow and roadmap.
4. `src/shotforge/core/project_state.py`: typed project state.
5. `src/shotforge/workflows/`: LangGraph workflow definitions.
6. `src/shotforge/agents/`: agent responsibilities.
7. `tests/`: behavior coverage.

## Why This Project Exists

AI video generation is not only a model-call problem. For complex creative output, the harder engineering problem is:

```text
plan -> generate/mock -> evaluate -> correct -> version -> converge -> export
```

ShotForge treats that loop as the product and engineering surface.

## Engineering Highlights

- Pydantic state model across the workflow.
- LangGraph orchestration.
- Mock generator for deterministic local testing.
- Evaluation rubrics and correction planning.
- Version snapshots and diffs.
- Trace logs.
- Exporters for JSON, CSV, Markdown, and evaluation reports.
- Chinese/English output support.
- Extension boundaries for MCP, sandboxing, and video model APIs.

## Product Highlights

- Web Demo for one-idea video planning.
- Storyboard and prompt package output.
- Evaluation and refinement surface.
- Exportable production package.
- Roadmap toward editable storyboard, TTS/subtitle planning, and MP4 preview rendering.

## How To Run

```powershell
pip install -e ".[dev]"
shotforge design "一只赛博猫在雨夜上海屋顶追逐发光无人机"
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
uvicorn shotforge.app.web.app:app --reload
```

## What This Project Demonstrates

- AI system design beyond prompt demos.
- Product thinking beyond framework integration.
- Ability to separate core architecture from product experience.
- Practical local-first development with mock providers and exportable artifacts.
