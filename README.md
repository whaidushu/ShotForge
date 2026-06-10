# ShotForge

ShotForge is a local-first workbench for building, running, evaluating, and
iterating AI video generation workflows.

It is not a video model. It is the workflow layer around video models: prompt
package generation, provider configuration, rendered artifact inspection,
layered evaluation, correction planning, version comparison, and handoff export.

```text
Idea -> Design -> Generate -> Observe -> Evaluate -> Correct -> Version -> Export
```

Docs: [English](docs/en/index.md) | [中文](docs/zh/index.md) | [All docs](docs/index.md)

## What It Does

ShotForge helps answer a practical question: after a video model returns a
result, how do you know whether it actually followed the creative brief, what
changed between iterations, and what should be fixed next?

The current implementation provides:

- a FastAPI Web workbench for creating and inspecting video-generation runs
- a Typer CLI for local automation
- typed `ProjectState` packages for reproducible run state
- provider profiles for LLM/Judge, Video, and Visual Observer services
- local video workflow discovery and API-format workflow execution
- frame extraction and visual observation hooks
- layered evaluation from concrete visual facts to style and atmosphere
- correction planning and iterative regeneration
- version snapshots, version diffs, score deltas, and regression checks
- JSON, CSV, Markdown, manifest, trace, run-summary, and evaluation exports
- English and Chinese UI/output support

## Why This Exists

AI video generation fails in ways that are hard to manage with a single prompt:
objects disappear, identities drift, actions change, locations are missed, and
style tweaks can regress basic physical requirements.

ShotForge treats video generation as a managed run:

1. structure the idea into scenes, shots, motion, audio, and prompt templates
2. render artifacts through a configured provider
3. observe frames instead of only reading prompt text
4. evaluate concrete targets before softer creative qualities
5. write correction plans and regenerate
6. keep version evidence and export a handoff package

## Quick Start

Create an environment and install the package:

```powershell
git clone https://github.com/whaidushu/ShotForge.git
cd ShotForge
conda create -n ShotForge python=3.11 pip -y
conda activate ShotForge
pip install -r requirements.txt
pip install -e .
```

Start the Web workbench:

```powershell
shotforge web --reload
```

Open:

```text
http://127.0.0.1:8000
```

Try the built-in demo when model services are not configured yet:

```text
http://127.0.0.1:8000/demo?language=en
```

Run a design-only CLI flow:

```powershell
shotforge design "A neon train crossing a desert at sunrise" --language en
```

Run a full loop with a configured provider:

```powershell
copy .env.example .env
shotforge doctor --deep
shotforge full-loop "A product reveal shot in a rainy city street" --language en --generator <provider-id>
```

Run the built-in effect demo:

```powershell
shotforge effect-demo cyber_cat_rooftop --language en --generator mock
```

The effect demo creates a single-shot v1/v2/v3 run for a concrete
physical-target case: v1 uses the raw user prompt, v2 applies a translated
structured prompt, and v3 is treated as a candidate compensation pass after
frame observation. The report records target-level deltas, preservation locks,
candidate acceptance or rejection, and the accepted iteration. Use a real
generator provider when ComfyUI or another video backend is configured.

The same physical-convergence primitives are used by the main redesign flow:
physical-effect issues produce target-level repair plans, preservation locks,
and candidate gates. The demo remains a packaged example case; the convergence
logic lives in the core workflow layer.

More setup details are in [Getting Started](docs/en/getting-started.md) and
[Configuration](docs/en/configuration.md).

## Web Workflow

The Web workbench is organized around runs:

1. configure provider profiles
2. run preflight checks
3. create a run from one idea
4. inspect storyboard and prompt package
5. inspect generated artifacts
6. compare observations and evaluation issues
7. inspect version changes
8. export the run package

Effect demo runs also expose a comparison page:

```text
/runs/<run_id>/effect-comparison
```

Do not open `src/shotforge/templates/index.html` directly in a browser. The UI
must be served through FastAPI/Jinja.

## CLI

Common commands:

```powershell
shotforge design "idea" --language en
shotforge full-loop "idea" --language en --redesign --max-iterations 3 --generator <provider-id>
shotforge effect-demo cyber_cat_rooftop --language en --generator <provider-id>
shotforge inspect data/runs/{run_id}/package.json
shotforge audit data/runs/{run_id}/package.json
shotforge capabilities
shotforge doctor --deep
shotforge web --reload
```

## API Example

```http
POST /api/runs
Content-Type: application/json

{
  "idea": "A cinematic AI video idea",
  "style": "cinematic",
  "language": "en",
  "duration_seconds": 24,
  "with_evaluation": true,
  "rubric_id": "baseline_v1",
  "provider_profile_id": "local-profile",
  "generator_provider_id": "<video-provider-id>",
  "observer_provider_id": "<observer-provider-id>"
}
```

Useful local endpoints:

```http
GET /api/health
GET /api/capabilities
GET /api/provider-profiles
POST /api/provider-profiles
POST /api/preflight
POST /api/runs
GET /api/runs
GET /api/runs/{run_id}/workbench
GET /api/runs/{run_id}/generation-artifacts
GET /api/runs/{run_id}/runtime-evidence
GET /api/runs/{run_id}/export/json
```

See [API Reference](docs/en/api-reference.md) for request fields, response
shapes, artifact downloads, and export formats.

## Output

Run outputs are written under:

```text
data/runs/{run_id}
```

Typical files include:

- `package.json`
- `package_view.json`
- `package.csv`
- `package.md`
- `manifest.json`
- `trace.json`
- `run_summary.md`
- `evaluation.csv`
- generated videos
- prompt text and prompt JSON
- provider workflow payloads
- extracted frames

Version snapshots are stored under `data/versions`.

## Architecture

```text
src/shotforge/
  app/          Web, API, CLI, and shared app services
  agents/       design, evaluation, correction, structuring, export agents
  core/         state, packages, context, trace, versioning, runtime evidence
  evaluators/   physical, consistency, static, and provider-backed evaluators
  exporters/    JSON, CSV, Markdown, manifest, trace, and report exporters
  generators/   video generator provider contracts and adapters
  observation/  frame extraction, frame observers, sequence observation
  workflows/    LangGraph workflow definitions
  i18n/         English and Chinese labels/output text
  knowledge/    rubrics, templates, prompt-support assets
tests/          API, CLI, provider, evaluator, workflow, and UI tests
docs/           English and Chinese project documentation
```

The main state contract is `ProjectState`. It connects the user idea, design
package, prompt package, generation artifacts, observations, evaluation reports,
correction plans, version diffs, traces, and exports.

See [Architecture](docs/en/architecture.md) for module-level details.

## Documentation

- [Getting Started](docs/en/getting-started.md)
- [Configuration](docs/en/configuration.md)
- [Architecture](docs/en/architecture.md)
- [Providers](docs/en/providers.md)
- [Evaluation](docs/en/evaluation.md)
- [API Reference](docs/en/api-reference.md)
- [Development](docs/en/development.md)
- [Change Log](docs/en/changelog.md)

中文文档入口：[docs/zh/index.md](docs/zh/index.md)

## Development

```powershell
pip install -e ".[dev]"
ruff check src tests
pytest -q
```

## Current Scope

ShotForge is local-first. It currently focuses on workflow execution,
inspection, evaluation, and artifact packaging. Production deployment concerns
such as authentication, multi-user tenancy, queueing, quota management, durable
object storage, and hosted observability are outside the default local setup.

## License

MIT License. See [LICENSE](LICENSE).
