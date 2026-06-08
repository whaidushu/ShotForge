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
- Internal test provider kept behind a dedicated test-chain control
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
  evaluators/          Evaluator interfaces and mock/static evaluators
  exporters/           JSON, CSV, Markdown, evaluation CSV exporters
  generators/          Test and real video generator providers
  observation/         Frame extraction, VLM/heuristic observation, sequence continuity
  workflows/           LangGraph workflows
  i18n/                Chinese / English labels and output text
  knowledge/           Rubrics, motion templates, audio patterns, prompt rules
tests/                 Pipeline, API, i18n, generator, evaluator tests
docs/                  Track definitions and review guide
```

## Track Documents

- [Architecture Overview](docs/architecture-overview.md): one-page map of workflow, runtime, interfaces, and deliverables.
- [Change Log](docs/CHANGELOG.md): implementation milestones and delivery-chain changes.
- [UI Engineering Framework](docs/ui-engineering-framework.md): Web UI asset, style, motion, icon, and layout organization.
- [Project Spine And Demo Path](docs/project-spine-and-demo-path.md): concise project framing, demo sequence, and review path.
- [Engineering Track](docs/engineering-track.md): architecture, engineering value, and implementation surface.
- [Agent Infra Runtime](docs/agent-infra-runtime.md): MCP-like adapter, sandbox policy, memory store, tool records, and runtime snapshots.
- [Harness Audit API](docs/harness-audit-api.md): run-level API for contexts, tool calls, policies, readiness, and solution evidence.
- [Capability Catalog API](docs/capability-catalog.md): provider catalog, playbooks, export formats, API routes, and Agent Infra capabilities.
- [Delivery Readiness](docs/delivery-readiness.md): POC gates, handoff deliverables, next actions, and production boundaries.
- [Industry Solution Playbooks](docs/industry-solution-playbooks.md): reusable scenario knowledge assets used by the solution architect agent.
- [POC Deployment Notes](docs/deployment-poc.md): local setup, CLI/Web demo, exports, storage layout, and production boundaries.
- [Volcengine JD Alignment](docs/volcengine-jd-alignment.md): how the project maps to the target AI Agent solution architect role.
- [Solution Blueprint](docs/solution-blueprint.md): customer-facing solution architecture and POC acceptance criteria.
- [Demo Script](docs/demo-script.md): 5-8 minute walkthrough for solution demos.
- [Sales Demo Playbook](docs/sales-demo-playbook.md): customer-facing demo narrative, objection handling, and evidence checklist.
- [POC Test Strategy](docs/poc-test-strategy.md): acceptance gates, test phases, and production exit criteria.
- [Model Selection Matrix](docs/model-selection-matrix.md): LLM/Judge, video, and observer provider selection tradeoffs.
- [Knowledge Assets](docs/knowledge-assets.md): reusable playbooks, rubrics, prompt rules, and solution templates.
- [Advertising Solution](docs/solutions/advertising-agent-solution.md): industry package for brand marketing and campaign video production.
- [E-commerce Solution](docs/solutions/ecommerce-video-agent-solution.md): industry package for product short-video workflows.
- [Game Trailer Solution](docs/solutions/game-trailer-agent-solution.md): industry package for game character and trailer ideation.
- [Product Track](docs/product-track.md): product goal, user workflow, UX milestones, and video creation loop.
- [Repository Review Guide](docs/repository-review-guide.md): how a reviewer should read this project in 5-10 minutes.
- [Roadmap](ROADMAP.md): longer-term technical roadmap and planned milestones.

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
[docs/deployment-poc.md](docs/deployment-poc.md) for Ollama, vLLM, ComfyUI, VLM,
and workflow-discovery setup, and
[docs/model-selection-matrix.md](docs/model-selection-matrix.md) for provider
selection tradeoffs.

LLM/Judge providers decide and revise text. Video providers render MP4 artifacts.
Visual observer providers inspect rendered frames so evaluators can check what
actually appeared in the video. The Web configuration page exposes these as
separate provider settings, and Run Preflight checks LLM, ComfyUI, workflow, and
observer readiness before real generation.

ComfyUI generation artifacts are written by iteration, with readable filenames:

```text
{runs_dir}/{run_id}/iterations/
  v001/
    prompts/
      v001_shot_01_hook.txt
      v001_shot_01_hook.json
    workflows/
      v001_shot_01_hook.api.json
    videos/
      v001_shot_01_hook.mp4
  v002/
    prompts/
      v002_shot_01_hook.txt
      v002_shot_01_hook.json
    workflows/
      v002_shot_01_hook.api.json
    videos/
      v002_shot_01_hook.mp4
```

`runs_dir` is `data/runs` by default and can be changed with
`SHOTFORGE_RUNS_DIR`. The final template package still writes
`package.json`, exports, traces, and evaluation reports at the run root.

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

Run outputs are written under `data/runs/{run_id}` by default.

The Web UI now has three local delivery controls:

- **Provider Profile**: save and reuse LLM/Judge and Video provider settings.
  Profiles are stored in `data/provider_profiles.json`.
- **Run Preflight**: check provider configuration before generation. For ComfyUI
  this validates server reachability and whether the selected workflow is
  API-callable.
- **Recent Runs**: reopen recent generated packages from the left sidebar.

Useful local APIs:

```http
GET /api/provider-profiles
POST /api/provider-profiles
GET /api/observer-providers
POST /api/preflight
POST /api/test-chain
GET /api/comfyui/workflows
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
  "generator_provider_id": "comfyui",
  "comfyui_base_url": "http://127.0.0.1:8188",
  "comfyui_workflow_id": "wan2_2_i2v_empty_start",
  "observer_provider_id": "prompt-proxy"
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

ShotForge is not trying to be a single-prompt video model. It is a production workbench and product prototype around video creation:

```text
Idea -> Design -> Generate -> Evaluate -> Correct -> Version -> Export
```

The current stage prioritizes workflow quality, structured state, real local provider integration, evaluation loops, version governance, and extension boundaries. The internal test provider exists only as a deployment diagnostic path.

## Current Framework Boundary

ShotForge is now organized around four replaceable provider surfaces:

- **LLM/Judge provider**: text reasoning, prompt evaluation, and redesign support.
- **Video provider**: ComfyUI or another renderer that produces MP4 artifacts.
- **Visual observer provider**: frame-level VLM inspection used by physical and consistency evaluators.
- **Internal test chain**: explicit deployment diagnostic path, not the default product flow.

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
