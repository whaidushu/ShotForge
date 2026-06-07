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

Run the evaluation and redesign loop with a real OpenAI-compatible LLM judge:

```powershell
copy .env.example .env
# Edit .env and set:
# SHOTFORGE_LLM_PROVIDER=openai-compatible
# SHOTFORGE_LLM_MODEL=your-model-name
# SHOTFORGE_LLM_BASE_URL=https://api.example.com/v1
# SHOTFORGE_LLM_API_KEY=your-api-key
# SHOTFORGE_EVALUATOR_MODE=hybrid

shotforge full-loop "A quiet revenge reveal in a luxury elevator" --language en --redesign --max-iterations 2
```

`SHOTFORGE_EVALUATOR_MODE=hybrid` keeps the deterministic mock/static
evaluators and adds an LLM-as-judge evaluator for storyboard and prompt quality.
Use `SHOTFORGE_EVALUATOR_MODE=llm` only when a real LLM provider is configured.

Local LLM options use the same evaluation loop.

For Ollama:

```powershell
# Windows install:
# irm https://ollama.com/install.ps1 | iex

ollama pull qwen2.5:7b
ollama serve

# .env
SHOTFORGE_LLM_PROVIDER=ollama
SHOTFORGE_LLM_MODEL=qwen2.5:7b
SHOTFORGE_LLM_BASE_URL=http://localhost:11434/v1
SHOTFORGE_EVALUATOR_MODE=hybrid

shotforge full-loop "A quiet revenge reveal in a luxury elevator" --language en --redesign --max-iterations 2
```

For a local vLLM OpenAI-compatible server:

Start vLLM in WSL/Linux. On a 16 GB GPU, `Qwen2.5-3B-Instruct` leaves enough
headroom for the evaluation loop while still exercising a real local model.

```bash
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate
python -m pip install --upgrade pip
python -m pip install vllm

export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
export VLLM_USE_FLASHINFER_SAMPLER=0

python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-3B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.75 \
  --max-model-len 4096
```

Then run ShotForge from Windows/PowerShell:

```powershell
# .env
SHOTFORGE_LLM_PROVIDER=vllm
SHOTFORGE_LLM_MODEL=Qwen/Qwen2.5-3B-Instruct
SHOTFORGE_LLM_BASE_URL=http://127.0.0.1:8000/v1
SHOTFORGE_LLM_API_KEY=local
SHOTFORGE_EVALUATOR_MODE=hybrid

shotforge full-loop "A quiet revenge reveal in a luxury elevator" --language en --redesign --max-iterations 2
```

### Visual Observer / VLM setup

LLM/Judge providers decide and revise text. Video providers render video.
Visual observer providers inspect rendered frames so evaluators can check what
actually appeared in the MP4.

The default `prompt-proxy` observer is a local diagnostic fallback: it reads the
prompt/package text and keeps the evaluation loop runnable without a vision
model. For real visual checks, configure one of the VLM observers.

For Ollama vision:

```powershell
ollama pull qwen2.5vl:7b
ollama serve

$env:SHOTFORGE_OBSERVER_PROVIDER="ollama-vision"
$env:SHOTFORGE_VLM_MODEL="qwen2.5vl:7b"
$env:SHOTFORGE_VLM_BASE_URL="http://localhost:11434"
$env:SHOTFORGE_VLM_FRAME_SAMPLE_COUNT="4"
$env:SHOTFORGE_VLM_CONFIDENCE_THRESHOLD="0.65"
```

For a local vLLM VLM OpenAI-compatible endpoint:

```powershell
$env:SHOTFORGE_OBSERVER_PROVIDER="vllm-vlm"
$env:SHOTFORGE_VLM_MODEL="Qwen/Qwen2.5-VL-7B-Instruct"
$env:SHOTFORGE_VLM_BASE_URL="http://127.0.0.1:8000/v1"
$env:SHOTFORGE_VLM_API_KEY="local"
```

The Web configuration page exposes the same settings under Visual Observer.
Use Run Preflight before real generation to check LLM, ComfyUI, workflow, and
observer service readiness.

Run with a real local ComfyUI video provider:

The bundled ComfyUI workflow `wan2_2_i2v_empty_start` uses local Wan2.2
image-to-video nodes. It creates a generated start frame inside ComfyUI, then
saves each generated shot as an MP4. On the ComfyUI desktop app, the backend is
commonly `http://127.0.0.1:8001`; standalone ComfyUI is commonly
`http://127.0.0.1:8188`.

Required local models for the bundled workflow:

- `models/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- `models/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`
- `models/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors`
- `models/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors`
- `models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- `models/vae/wan_2.1_vae.safetensors`

```powershell
# Start ComfyUI first, then set:
$env:SHOTFORGE_COMFYUI_ENABLED="true"
$env:SHOTFORGE_COMFYUI_BASE_URL="http://127.0.0.1:8001"
$env:SHOTFORGE_COMFYUI_WORKFLOWS_DIR="C:\Users\your-name\Documents\ComfyUI\user\default\workflows"
$env:SHOTFORGE_COMFYUI_WORKFLOW_ID="wan2_2_i2v_empty_start"
$env:SHOTFORGE_COMFYUI_WIDTH="320"
$env:SHOTFORGE_COMFYUI_HEIGHT="320"
$env:SHOTFORGE_COMFYUI_LENGTH="9"
$env:SHOTFORGE_COMFYUI_FPS="8"
$env:SHOTFORGE_COMFYUI_TIMEOUT_SECONDS="1200"

# Optional: cap real generation during local smoke tests.
$env:SHOTFORGE_COMFYUI_MAX_SHOTS="1"

shotforge full-loop "A design director reviews a repaired AI storyboard in a midnight studio" --language en --generator comfyui --redesign --max-iterations 1
```

Set `SHOTFORGE_COMFYUI_MAX_SHOTS=0` or leave it unset to generate every shot.
At 320x320 and 9 frames, the smoke-test path is intended to exercise integration,
artifact tracking, versioned iterations, and evaluation flow rather than final visual quality.

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

To run the full real generation loop instead of a one-shot smoke test:

```powershell
$env:SHOTFORGE_COMFYUI_MAX_SHOTS="0"
shotforge full-loop "A rushed AI storyboard demo starts with a vague broken concept, then the agent repairs it into a clear cinematic launch scene" --language en --generator comfyui --redesign --max-iterations 1
```

Query available ComfyUI workflows:

```powershell
shotforge comfyui-workflows
shotforge comfyui-workflows --root "C:\Users\your-name\Documents\ComfyUI\user\default\workflows"
```

Local workflow files are exposed with ids like `local:my_workflow` or
`local:folder/my_workflow`. Only API-format ComfyUI JSON can be sent to
`/prompt`; normal UI graph exports are listed as `ui_graph` and must be saved
from ComfyUI in API format before ShotForge can call them. A local API workflow
can use placeholders such as `{{prompt}}`, `{{negative_prompt}}`, `{{shot_id}}`,
`{{width}}`, `{{height}}`, `{{length}}`, `{{fps}}`, `{{seed}}`, and
`{{filename_prefix}}`.

```powershell
$env:SHOTFORGE_COMFYUI_WORKFLOW_ID="local:my_workflow"
shotforge full-loop "A cinematic product reveal" --language en --generator comfyui

# Or point directly to an API-format JSON file:
$env:SHOTFORGE_COMFYUI_WORKFLOW_ID="file:C:\path\to\workflow_api.json"
shotforge full-loop "A cinematic product reveal" --language en --generator comfyui
```

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

ShotForge is not trying to be a single-prompt video model. It is a workflow harness and product prototype around video creation:

```text
Idea -> Design -> Generate -> Evaluate -> Correct -> Version -> Export
```

The current stage prioritizes workflow quality, structured state, real local provider integration, evaluation loops, and extension boundaries. The internal test provider exists only as a deployment diagnostic path.

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
