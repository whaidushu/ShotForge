# ShotForge

ShotForge is a local-first AI video Agent Workbench that explores how an agent runtime, an evaluation loop, and workflow version governance can support the full path from creative idea to prompt package, video artifact, quality review, iteration, and handoff export.

It has two deliberately separated tracks:

1. **Engineering Runtime**: an agent orchestration system for stateful workflow execution, provider boundaries, evaluation, traceability, and versioned iteration.
2. **Product Studio**: a user-facing short-video creation workflow for provider configuration, local service checks, generation, prompt review, artifact preview, and export.

The current default branch keeps both layers connected: the runtime manages structured state, agents, evaluation, traces, version snapshots, and version diffs; the Web product layer lets a user configure providers, test local services, run generation, inspect prompt changes, compare versions, and open video artifacts.

## Why Two Tracks

Building an impressive engineering project and building a complete product are not the same job.

The engineering track explores:

- Can the system model state clearly?
- Can agents be orchestrated, traced, evaluated, versioned, and extended?
- Can model providers, tools, evaluators, and correction agents be plugged in without rewriting the workflow?

The product track explores:

- Can a user start from one idea and get a usable short-video output?
- Can they review, edit, refine, preview, and export without reading implementation details?
- Can the workflow feel like a real creative tool instead of a technical demo?

Keeping these tracks explicit makes the project easier to review, easier to extend, and easier to evolve without mixing runtime architecture decisions with product-surface decisions.

## Current Capability

ShotForge currently supports:

- FastAPI Web product workflow
- Typer CLI
- LangGraph workflows
- Pydantic project state
- Context building and lightweight knowledge base
- Skill/tool registry
- Version snapshots and version diffs
- Run history, prompt changes, and version-chain inspection
- Trace logging
- Evaluation and correction planning
- Provider profiles for LLM/Judge and Video generation settings
- Local Ollama / vLLM / OpenAI-compatible LLM evaluation
- Local ComfyUI workflow discovery and API-format workflow execution
- Visual observer provider profiles for prompt-proxy, OpenAI-compatible vision, Ollama vision, and vLLM VLM inspection
- Physical target extraction for hard visual facts such as subject count, required objects, location, weather, and action
- Frame extraction, frame observation, sequence observation, and evaluator-ready video observations
- JSON / CSV / Markdown / manifest / trace / run-summary exports
- Chinese and English output
- Extension boundaries for MCP, sandboxing, and external video model APIs

## Repository Map

```text
src/shotforge/
  app/                 CLI and FastAPI Web entrypoints
    services/          Shared run, provider, and artifact services
    web/static/        UI tokens, shared styles, and browser behavior
  agents/              Design, evaluation, correction, structuring, export agents
  core/                ProjectState, ContextBuilder, TraceLog, VersionManager, rubrics
  evaluators/          Evaluator interfaces, static checks, and provider-backed evaluators
  exporters/           JSON, CSV, Markdown, evaluation CSV exporters
  generators/          Test and real video generator providers
  observation/         Frame extraction, VLM/heuristic observation, sequence continuity
  workflows/           LangGraph workflows
  i18n/                Chinese / English labels and output text
  knowledge/           Rubrics, motion templates, audio patterns, prompt rules
tests/                 Pipeline, API, i18n, generator, evaluator tests
docs/                  Bilingual documentation index plus en/ and zh/ documents
```

## Reading Path

- [Documentation Index](docs/index.md): Chinese and English documentation entrypoint.
- [Repository Review Guide](docs/en/repository-review-guide.md): how to read the project in 5-10 minutes.
- [Architecture Overview](docs/en/architecture-overview.md): one-page map of workflow, runtime, interfaces, and deliverables.
- [Project Spine And Demo Path](docs/en/project-spine-and-demo-path.md): concise framing, demo sequence, and review path.
- [Engineering Track](docs/en/engineering-track.md): architecture, engineering value, and implementation surface.
- [Product Track](docs/en/product-track.md): product goal, user workflow, UX milestones, and video creation loop.
- [Deployment Notes](docs/en/local-deployment.md): local setup, provider configuration, exports, and storage layout.
- [Model Selection Matrix](docs/en/model-selection-matrix.md): LLM/Judge, video, and observer provider selection tradeoffs.

## Quick Start

### Conda setup

From a fresh clone, create and activate a dedicated Conda environment:

```powershell
cd D:\Github\ShotForge\ShotForge
conda create -n ShotForge python=3.11 pip -y
conda activate ShotForge
pip install -r requirements.txt
pip install -e .
```

`requirements.txt` is a pinned dependency snapshot generated from a working
`ShotForge` Conda environment. `pyproject.toml` remains the source of the
package metadata, editable install entry point, and dependency ranges.

If PowerShell blocks `conda activate`, run the commands from Anaconda Prompt or
run `conda init powershell`, then reopen the terminal.

Verify the install:

```powershell
python -m pytest
shotforge doctor
shotforge doctor --deep
```

Run the design pipeline from the CLI:

```powershell
shotforge design "A cyber cat chases a glowing drone across rainy Shanghai rooftops"
```

Run a Windows local demo with package generation and audit output:

```powershell
.\scripts\demo.ps1 -Language en
```

Run the full evaluation loop:

```powershell
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
```

Run with iterative redesign:

```powershell
shotforge full-loop "A cyber cat chases a glowing drone across rainy Shanghai rooftops" --redesign --max-iterations 3
```

The full-loop path is now:

```text
Idea
-> design package
-> prompt and structured template
-> video provider render
-> frame extraction / observation
-> layered evaluation
-> correction plan
-> optimized prompt/template package
-> regenerated video
-> version diff / run history
-> exports and run summary
```

The first convergence layer is intentionally physical: it checks whether the
generated result contains the visible elements requested by the user before
spending effort on style, atmosphere, or narrative polish. For example,
`A cyber cat chases a glowing drone across rainy Shanghai rooftops` is expanded
into hard targets such as `cyber cat`, `glowing drone`, `rainy night`,
`Shanghai`, `rooftop`, and `chasing`.

When a visual observer is configured, the evaluation report records a physical
target summary: required elements, observed elements, missing elements, observer
source, and hard physical issue count. Correction plans use that summary to
rewrite prompts around concrete missing objects or scene anchors instead of
only adding broad descriptive style language.

Run the evaluation and redesign loop with a configured provider profile:

```powershell
copy .env.example .env
shotforge doctor --deep

shotforge full-loop "A quiet revenge reveal in a luxury elevator" --language en --redesign --max-iterations 2
```

`SHOTFORGE_EVALUATOR_MODE=hybrid` keeps deterministic/static checks and adds an
LLM-as-judge evaluator for storyboard and prompt quality. Use
`SHOTFORGE_EVALUATOR_MODE=llm` only when a real LLM provider is configured.

Provider setup is intentionally kept out of the README. See
[docs/en/local-deployment.md](docs/en/local-deployment.md) for Ollama, vLLM, ComfyUI, VLM,
and workflow-discovery setup, and
[docs/en/model-selection-matrix.md](docs/en/model-selection-matrix.md) for provider
selection tradeoffs.

LLM/Judge providers decide and revise text. Video providers render MP4 artifacts.
Visual observer providers inspect rendered frames so evaluators can check what
actually appeared in the video. The Web configuration page exposes these as
separate provider settings, and Run Preflight checks provider readiness before
real generation.

Run outputs are written under `data/runs/{run_id}` by default. Iteration-level
prompts, workflow payloads, video artifacts, exports, traces, and evaluation
reports are kept together so each generation can be reviewed and compared.

Start the Web Demo:

```powershell
shotforge web --reload
```

Open:

```text
http://127.0.0.1:8000
```

Do not open `src/shotforge/templates/index.html` directly in a browser and do
not serve the template directory with a static file server. The Web UI must be
served through FastAPI/Jinja; otherwise raw template expressions such as
`{{ form_state.style }}` will appear instead of rendered values.

The Web UI now has three local delivery controls:

- **Provider Profile**: save and reuse LLM/Judge and Video provider settings.
  Profiles are stored in `data/provider_profiles.json`.
- **Run Preflight**: check provider configuration before generation.
- **Recent Runs**: reopen recent generated packages from the left sidebar.

Useful local APIs:

```http
GET /api/provider-profiles
POST /api/provider-profiles
GET /api/observer-providers
POST /api/preflight
GET /api/runs
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
  "provider_profile_id": "local-real",
  "generator_provider_id": "comfyui",
  "observer_provider_id": "prompt-proxy"
}
```

Provider URLs, model names, workflow paths, and local service ports should be
saved through the Web configuration page, provider profiles, or environment
variables. Request-level provider overrides are supported for automation and
diagnostics, but they are documented in
[docs/en/local-deployment.md](docs/en/local-deployment.md), not in the main API example.

Exports:

```http
GET /api/runs/{run_id}/export/json
GET /api/runs/{run_id}/export/csv
GET /api/runs/{run_id}/export/markdown
GET /api/runs/{run_id}/export/evaluation_csv
```

Run IDs use local time, for example `20260520_1452`. If multiple runs are created in the same minute, ShotForge appends `_02`, `_03`, and so on.

## What This Is Not

ShotForge is not trying to be a single-prompt video model. It is a production workbench and product prototype around video creation:

```text
Idea -> Design -> Generate -> Evaluate -> Correct -> Version -> Export
```

The current stage prioritizes workflow quality, structured state, real local provider integration, evaluation loops, version governance, and extension boundaries.

## Current Framework Boundary

ShotForge is now organized around four replaceable provider surfaces:

- **LLM/Judge provider**: text reasoning, prompt evaluation, and redesign support.
- **Video provider**: ComfyUI or another renderer that produces MP4 artifacts.
- **Visual observer provider**: frame-level VLM inspection used by physical and consistency evaluators.

This split keeps the product workflow understandable for users while keeping the
engineering framework open for future models, hosted services, and stronger
evaluation layers.

## Development

```powershell
python -m pytest
python -m ruff check src tests
```

## License

MIT License. See [LICENSE](LICENSE).
