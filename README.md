# ShotForge

ShotForge is a local-first AI video workbench built on top of an inspectable
Agent Harness runtime. It explores how state management, context engineering,
tool orchestration, evaluation loops, provider boundaries, and workflow version
governance can support the path from creative idea to prompt package, video
artifact, quality review, iteration, and handoff export.

Documentation: [Docs index](docs/index.md)

## Architecture Layers

ShotForge has two connected layers:

1. **Agent Harness Runtime**: the orchestration layer for typed state,
   context construction, agent contracts, skill/tool orchestration, memory,
   MCP-style access, sandbox policy, evaluation, traceability, and versioned
   iteration.
2. **AI Video Workbench**: the user-facing layer for provider configuration,
   local service checks, run creation, storyboard and prompt review, generated
   artifacts, evaluation results, version comparison, and handoff export.

The Web workbench is the product surface. The Agent Harness runtime is the
inspectable execution layer underneath it.

## Why This Shape

AI video generation is not only a single model-call problem. For a production
workflow, the harder problem is managing the loop around the model:

```text
idea -> design -> generate -> observe -> evaluate -> correct -> version -> export
```

ShotForge keeps the runtime and workbench separated so the system can be
reviewed in two ways: as an Agent Harness architecture and as a usable video
production workspace.

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

- [Documentation Index](docs/index.md): documentation entrypoint with English and Chinese links.
- [Getting Started](docs/en/getting-started.md): install, run the Web app, and try the demo.
- [Configuration](docs/en/configuration.md): environment variables, provider profiles, and local services.
- [Architecture](docs/en/architecture.md): runtime, workbench, state, and artifact flow.
- [Providers](docs/en/providers.md): LLM/Judge, video, and visual observer providers.
- [Evaluation](docs/en/evaluation.md): physical targets, frame observation, and layered scoring.
- [API Reference](docs/en/api-reference.md): core Web API and CLI entrypoints.
- [Development](docs/en/development.md): local development, tests, and extension points.

## Demo Path

For a quick public walkthrough, start with the Web workbench:

1. Run `shotforge web --reload`.
2. Open `http://127.0.0.1:8000/demo?language=en` to load the curated sample run.
3. Inspect the run overview, storyboard, prompt package, generation artifacts,
   evaluation, version changes, exports, and harness evidence.
4. Open Configuration to check how LLM/Judge, Video, and Visual Observer
   providers are separated and preflighted.
5. Create a new run from the left rail to see how the same workflow starts from
   one idea.

This path presents ShotForge as a run-management workbench first, with the Agent
Harness evidence available as the inspection layer underneath.

## Quick Start

### Conda setup

From a fresh clone, create and activate a dedicated Conda environment:

```powershell
git clone https://github.com/whaidushu/ShotForge.git
cd ShotForge
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
[docs/en/configuration.md](docs/en/configuration.md) for environment variables,
provider profiles, and workflow discovery, and
[docs/en/providers.md](docs/en/providers.md) for provider selection tradeoffs.

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
[docs/en/configuration.md](docs/en/configuration.md), not in the main API example.

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

ShotForge is now organized around three replaceable provider surfaces:

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
