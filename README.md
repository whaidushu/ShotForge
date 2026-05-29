# ShotForge

ShotForge is an AI video creative agent project with two deliberately separated tracks:

1. **Engineering Harness**: an agent orchestration system that demonstrates production-grade AI engineering practices.
2. **Product Studio**: a user-facing short-video creation workflow that focuses on product completeness and end-to-end usability.

The current default branch is intentionally closer to the Engineering Harness track. The Product Studio track is being designed as a product layer on top of the same core assets.

## Why Two Tracks

Building an impressive engineering project and building a complete product are not the same job.

The engineering track answers:

- Can the system model state clearly?
- Can agents be orchestrated, traced, evaluated, versioned, and extended?
- Can model providers, tools, evaluators, and correction agents be plugged in without rewriting the workflow?

The product track answers:

- Can a user start from one idea and get a usable short-video output?
- Can they review, edit, refine, preview, and export without reading implementation details?
- Can the workflow feel like a real creative tool instead of a technical demo?

Keeping these tracks explicit makes the project easier to review, easier to extend, and easier to explain in interviews.

## Current Capability

ShotForge currently supports:

- FastAPI Web Demo
- Typer CLI
- LangGraph workflows
- Pydantic project state
- Context building and lightweight knowledge base
- Skill/tool registry
- Version snapshots and version diffs
- Trace logging
- Evaluation and correction planning
- Mock generator provider
- JSON / CSV / Markdown exports
- Chinese and English output
- Extension placeholders for MCP, sandboxing, and external video model APIs

## Repository Map

```text
src/shotforge/
  app/                 CLI and FastAPI Web entrypoints
  agents/              Design, evaluation, correction, structuring, export agents
  core/                ProjectState, ContextBuilder, TraceLog, VersionManager, rubrics
  evaluators/          Evaluator interfaces and mock/static evaluators
  exporters/           JSON, CSV, Markdown, evaluation CSV exporters
  generators/          Mock and planned video generator providers
  workflows/           LangGraph workflows
  extensions/          MCP, sandbox, review/refine, video API extension boundaries
  i18n/                Chinese / English labels and output text
  knowledge/           Rubrics, motion templates, audio patterns, prompt rules
tests/                 Pipeline, API, i18n, generator, evaluator tests
docs/                  Track definitions and review guide
```

## Track Documents

- [Architecture Overview](docs/architecture-overview.md): one-page map of workflow, runtime, interfaces, and deliverables.
- [Project Spine And Demo Path](docs/project-spine-and-demo-path.md): concise project framing, demo sequence, and what the demo should prove.
- [Engineering Track](docs/engineering-track.md): architecture, engineering value, and implementation surface.
- [Agent Infra Runtime](docs/agent-infra-runtime.md): MCP-like adapter, sandbox policy, memory store, tool records, and runtime snapshots.
- [Harness Audit API](docs/harness-audit-api.md): run-level API for contexts, tool calls, policies, readiness, and solution evidence.
- [Capability Catalog API](docs/capability-catalog.md): provider catalog, playbooks, export formats, API routes, and Agent Infra capabilities.
- [Delivery Readiness](docs/delivery-readiness.md): POC gates, handoff deliverables, next actions, and production boundaries.
- [Industry Solution Playbooks](docs/industry-solution-playbooks.md): reusable scenario knowledge assets used by the solution architect agent.
- [POC Deployment Notes](docs/deployment-poc.md): local setup, CLI/Web demo, exports, storage layout, and production boundaries.
- [Volcengine JD Alignment](docs/volcengine-jd-alignment.md): how the project maps to the target AI Agent solution architect role.
- [Solution Blueprint](docs/solution-blueprint.md): customer-facing solution architecture and POC acceptance criteria.
- [Demo Script](docs/demo-script.md): 5-8 minute walkthrough for interviews or solution demos.
- [Product Track](docs/product-track.md): product goal, user workflow, UX milestones, and video creation loop.
- [Resume Review Guide](docs/resume-review-guide.md): how a reviewer should read this project in 5-10 minutes.
- [Roadmap](ROADMAP.md): longer-term technical roadmap and planned milestones.

## Quick Start

```powershell
cd D:\Git\ShotForge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Run the design pipeline:

```powershell
shotforge design "一只赛博猫在雨夜上海屋顶追逐发光无人机"
```

Run a Windows local demo with package generation and harness audit:

```powershell
.\scripts\demo.ps1 -Language en
```

Run the full evaluation loop:

```powershell
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
```

Run with iterative redesign:

```powershell
shotforge full-loop "一只赛博猫在雨夜上海屋顶追逐发光无人机" --redesign --max-iterations 3
```

Start the Web Demo:

```powershell
uvicorn shotforge.app.web.app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## API Example

```http
POST /api/runs
Content-Type: application/json

{
  "idea": "A cinematic AI video idea",
  "style": "cinematic",
  "language": "zh",
  "duration_seconds": 24,
  "with_evaluation": true,
  "rubric_id": "baseline_v1",
  "generator_provider_id": "mock"
}
```

Exports:

```http
GET /api/runs/{run_id}/export/json
GET /api/runs/{run_id}/export/csv
GET /api/runs/{run_id}/export/markdown
GET /api/runs/{run_id}/export/evaluation_csv
```

Run IDs use local time, for example `20260520_1452`. If multiple runs are created in the same minute, ShotForge appends `_02`, `_03`, and so on.

## What This Is Not

ShotForge is not trying to be a single-prompt video model. It is a workflow harness and product prototype around video creation:

```text
Idea -> Design -> Generate/Mock -> Evaluate -> Correct -> Version -> Export
```

The current stage prioritizes workflow quality, structured state, evaluation loops, and extension boundaries. Real video model integration and MP4 rendering belong to the Product Studio roadmap.

## Development

```powershell
python -m pytest
python -m ruff check src tests
```

## License

MIT License. See [LICENSE](LICENSE).
