# POC Deployment Notes

ShotForge is currently a local-first POC. It is designed to run on a laptop for review, demos, and solution walkthroughs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

Copy the example environment file if you want explicit local paths:

```bash
copy .env.example .env
```

The default config writes runtime data under `data/`, which is ignored by git.

## CLI Demo

```bash
shotforge design "A neon train crossing a desert at sunrise" --language en
```

Windows one-command demo:

```powershell
.\scripts\demo.ps1 -Language en
```

Inspect the generated harness evidence:

```bash
shotforge audit data/runs/{run_id}/package.json
```

Inspect available agents, providers, playbooks, exports, and routes:

```bash
shotforge capabilities
```

Check local configuration and storage paths:

```bash
shotforge doctor
```

Run a deeper local readiness check before using real providers:

```bash
shotforge doctor --deep
```

Deep doctor checks the default provider profile, including LLM/Judge endpoint,
ComfyUI server, selected workflow, local workflow directory, and visual observer
configuration. It does not start those services for the user; it explains which
service, URL, model, or path still needs attention.

## Local Provider Setup

ShotForge separates model services by role:

- **LLM/Judge provider**: revises prompts and evaluates text/storyboard quality.
- **Video provider**: renders video artifacts, such as MP4 files from ComfyUI.
- **Visual observer provider**: inspects rendered frames so evaluation can check
  what actually appeared in the video.

The Web configuration page exposes these as separate settings. After changing
provider configuration, run `shotforge doctor --deep` or use Run Preflight in the
Web UI before starting a real generation run.

For normal API calls, prefer passing `provider_profile_id` and keep service URLs,
model names, and workflow ids in the saved profile or `.env`. Request-level
provider overrides are mainly for automation, diagnostics, and local smoke tests.

### OpenAI-Compatible LLM/Judge

Use this for hosted APIs, local gateway services, or vLLM OpenAI-compatible
servers:

```powershell
copy .env.example .env

# .env
SHOTFORGE_LLM_PROVIDER=openai-compatible
SHOTFORGE_LLM_MODEL=your-model-name
SHOTFORGE_LLM_BASE_URL=https://api.example.com/v1
SHOTFORGE_LLM_API_KEY=your-api-key
SHOTFORGE_EVALUATOR_MODE=hybrid
```

`SHOTFORGE_EVALUATOR_MODE=hybrid` keeps deterministic/static checks and adds an
LLM-as-judge evaluator. Use `SHOTFORGE_EVALUATOR_MODE=llm` only when the LLM
provider is ready.

### Ollama LLM/Judge

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
```

Then run:

```powershell
shotforge full-loop "A quiet revenge reveal in a luxury elevator" --language en --redesign --max-iterations 2
```

### vLLM LLM/Judge

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
```

### Visual Observer / VLM

The default `prompt-proxy` observer is a diagnostic fallback. It reads the
prompt/package text and keeps the loop runnable without a vision model. For real
visual checks, configure one of the VLM observers.

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

### ComfyUI Video Provider

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
```

Smoke-test the real ComfyUI integration:

```powershell
shotforge full-loop "A design director reviews a repaired AI storyboard in a midnight studio" --language en --generator comfyui --redesign --max-iterations 1
```

Set `SHOTFORGE_COMFYUI_MAX_SHOTS=0` or leave it unset to generate every shot. At
320x320 and 9 frames, the smoke-test path is intended to exercise integration,
artifact tracking, versioned iterations, and evaluation flow rather than final
visual quality.

Run the full real generation loop instead of a one-shot smoke test:

```powershell
$env:SHOTFORGE_COMFYUI_MAX_SHOTS="0"
shotforge full-loop "A rushed AI storyboard demo starts with a vague broken concept, then the agent repairs it into a clear cinematic launch scene" --language en --generator comfyui --redesign --max-iterations 1
```

### ComfyUI Workflow Discovery

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

## Web Demo

```bash
python -m uvicorn shotforge.app.web.app:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Useful API routes:

```text
POST /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/harness
GET /api/health
GET /api/runs/{run_id}/export/{format}
```

Supported export formats include:

- `json`
- `csv`
- `markdown`
- `manifest`
- `trace`
- `run_summary`
- `evaluation_csv`

## Storage Layout

```text
data/
  runs/{run_id}/
    package.json
    package.csv
    package.md
    manifest.json
    trace.json
    run_summary.md
    evaluation.csv
  versions/{project_id}/
  knowledge_base.json
  memory.jsonl
```

## Production Boundary

Before a real customer pilot, the following should be added:

- Docker or compose-based bootstrap for local LLM, ComfyUI, storage, and app services
- auth and tenant/project isolation
- production database or object storage
- official MCP transport if external tools are required
- stronger sandbox isolation, such as container execution
- real LLM/video provider credentials and quota controls
- observability, health checks, and deployment profiles
- customer-specific playbook overlays or RAG-backed knowledge retrieval

The current value of the POC is that these boundaries are explicit in state, readiness reports, docs, and audit exports.
