# Configuration

ShotForge can run with deterministic development providers or with local/remote
model providers. Configuration can be supplied through `.env`, provider
profiles, and the Web configuration page.

## Environment File

Start from:

```powershell
copy .env.example .env
```

Common settings:

```text
SHOTFORGE_LLM_PROVIDER=ollama
SHOTFORGE_LLM_MODEL=qwen2.5:7b
SHOTFORGE_LLM_BASE_URL=http://localhost:11434/v1
SHOTFORGE_EVALUATOR_MODE=hybrid
SHOTFORGE_VIDEO_PROVIDER=comfyui
SHOTFORGE_COMFYUI_BASE_URL=http://127.0.0.1:8188
```

Use `.env.example` as the source of truth for supported variables.

## Provider Profiles

Provider profiles group the settings for one runnable configuration:

- LLM/Judge provider
- Video provider
- Visual observer provider
- ComfyUI URL and workflow ID
- model names and API-compatible base URLs

Profiles can be edited from the Web configuration page or loaded by the API and
CLI. The Web app separates LLM/Judge, Video, and Visual Observer settings so
users can test each service independently.

## Preflight

Run preflight before real generation:

```powershell
shotforge doctor --deep
```

The Web app also exposes readiness checks for:

- reachable model endpoints
- ComfyUI server availability
- selected workflow existence
- provider profile completeness
- output and artifact paths

## ComfyUI Workflows

ShotForge expects API-format ComfyUI workflows. Bundled workflows and user-local
workflows can be discovered by the ComfyUI workflow service. When using a local
workflow, save the workflow selection in a provider profile before running a
full generation.
