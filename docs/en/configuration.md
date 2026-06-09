# Configuration

ShotForge can run with built-in test providers or with configured local/remote
model services. Configuration comes from three places:

1. `.env` settings loaded by `shotforge.config.Settings`.
2. Provider profiles stored in `data/provider_profiles.json`.
3. Request-level overrides from the Web form or API payload.

Provider profiles take precedence for normal runs. Request payloads can override
profile fields for automation.

## Environment File

Start from:

```powershell
copy .env.example .env
```

Use generic values in public examples and put real secrets only in your local
`.env`.

```text
SHOTFORGE_APP_NAME=ShotForge
SHOTFORGE_STORAGE_ROOT=data
SHOTFORGE_RUNS_DIR=data/runs
SHOTFORGE_VERSIONS_DIR=data/versions
SHOTFORGE_PROVIDER_PROFILES_PATH=data/provider_profiles.json

SHOTFORGE_LLM_PROVIDER=<llm-provider-id>
SHOTFORGE_LLM_MODEL=<model-name>
SHOTFORGE_LLM_BASE_URL=<openai-compatible-base-url>
SHOTFORGE_LLM_API_KEY=<api-key-if-required>
SHOTFORGE_EVALUATOR_MODE=hybrid

SHOTFORGE_COMFYUI_ENABLED=true
SHOTFORGE_COMFYUI_BASE_URL=<video-service-base-url>
SHOTFORGE_COMFYUI_WORKFLOWS_DIR=<path-to-api-workflows>
SHOTFORGE_COMFYUI_WORKFLOW_ID=<workflow-id>

SHOTFORGE_OBSERVER_PROVIDER=<observer-provider-id>
SHOTFORGE_VLM_MODEL=<vision-model-name>
SHOTFORGE_VLM_BASE_URL=<vision-base-url>
SHOTFORGE_VLM_API_KEY=<api-key-if-required>
```

## Storage Settings

| Variable | Purpose |
| --- | --- |
| `SHOTFORGE_STORAGE_ROOT` | Base data directory. |
| `SHOTFORGE_RUNS_DIR` | Run packages and generated artifacts. |
| `SHOTFORGE_VERSIONS_DIR` | Version snapshots. |
| `SHOTFORGE_KNOWLEDGE_BASE_PATH` | Local knowledge base JSON. |
| `SHOTFORGE_MEMORY_STORE_PATH` | Local JSONL memory store. |
| `SHOTFORGE_PROVIDER_PROFILES_PATH` | Provider profile JSON file. |

The app creates required directories on startup.

## LLM/Judge Settings

| Variable | Purpose |
| --- | --- |
| `SHOTFORGE_LLM_PROVIDER` | Provider id used for prompt generation and judge calls. |
| `SHOTFORGE_LLM_MODEL` | Model name understood by the provider. |
| `SHOTFORGE_LLM_BASE_URL` | Base URL for API-compatible providers. |
| `SHOTFORGE_LLM_API_KEY` | Optional API key. |
| `SHOTFORGE_LLM_TEMPERATURE` | Sampling temperature. |
| `SHOTFORGE_LLM_TIMEOUT_SECONDS` | Request timeout. |
| `SHOTFORGE_EVALUATOR_MODE` | `mock`, `llm`, or `hybrid`. |

Use `hybrid` when you want deterministic checks plus a configured judge model.

## Video Provider Settings

| Variable | Purpose |
| --- | --- |
| `SHOTFORGE_COMFYUI_ENABLED` | Enables the ComfyUI-backed video path. |
| `SHOTFORGE_COMFYUI_BASE_URL` | Video service base URL. |
| `SHOTFORGE_COMFYUI_WORKFLOWS_DIR` | Directory used for local workflow discovery. |
| `SHOTFORGE_COMFYUI_WORKFLOW_ID` | Selected API-format workflow id. |
| `SHOTFORGE_COMFYUI_TIMEOUT_SECONDS` | Render request timeout. |
| `SHOTFORGE_COMFYUI_WIDTH` | Render width. |
| `SHOTFORGE_COMFYUI_HEIGHT` | Render height. |
| `SHOTFORGE_COMFYUI_LENGTH` | Frame count or provider-specific length parameter. |
| `SHOTFORGE_COMFYUI_FPS` | Target frame rate. |
| `SHOTFORGE_COMFYUI_MAX_SHOTS` | Shot cap for local runs; `0` means no explicit cap. |

## Visual Observer Settings

| Variable | Purpose |
| --- | --- |
| `SHOTFORGE_OBSERVER_PROVIDER` | Visual observer provider id. |
| `SHOTFORGE_VLM_MODEL` | Vision model name. |
| `SHOTFORGE_VLM_BASE_URL` | Base URL for local or API-compatible VLMs. |
| `SHOTFORGE_VLM_API_KEY` | Optional API key. |
| `SHOTFORGE_VLM_FRAME_SAMPLE_COUNT` | Number of frames sampled per shot, 1-16. |
| `SHOTFORGE_VLM_CONFIDENCE_THRESHOLD` | Confidence threshold used by observation/evaluation. |
| `SHOTFORGE_VLM_REQUIRE_JSON` | Ask VLM endpoints for JSON responses when supported. |
| `SHOTFORGE_VLM_TIMEOUT_SECONDS` | Frame observation timeout. |

## Provider Profiles

Provider profiles are stored at `data/provider_profiles.json` by default. A
profile groups:

- LLM/Judge provider settings
- video provider settings
- visual observer settings
- workflow selection
- render parameters
- optional metadata

Secrets are redacted from API responses. `public_dict()` returns
`has_llm_api_key` and `has_vlm_api_key` flags instead of raw keys.

Example profile payload:

```json
{
  "profile_id": "local-profile",
  "name": "Local profile",
  "llm_provider_id": "<llm-provider-id>",
  "llm_model": "<model-name>",
  "llm_base_url": "<base-url>",
  "llm_api_key": "",
  "evaluator_mode": "hybrid",
  "generator_provider_id": "<video-provider-id>",
  "comfyui_base_url": "<video-service-base-url>",
  "comfyui_workflows_dir": "<workflow-directory>",
  "comfyui_workflow_id": "<workflow-id>",
  "comfyui_width": 320,
  "comfyui_height": 320,
  "comfyui_length": 9,
  "comfyui_fps": 8.0,
  "comfyui_max_shots": 0,
  "observer_provider_id": "<observer-provider-id>",
  "vlm_model": "<vision-model-name>",
  "vlm_base_url": "<vision-base-url>",
  "vlm_api_key": "",
  "vlm_frame_sample_count": 4,
  "vlm_confidence_threshold": 0.65,
  "vlm_require_json": true
}
```

Save it through:

```text
POST /api/provider-profiles
```

## Preflight

Run preflight before full generation:

```powershell
shotforge doctor --deep
```

or:

```text
POST /api/preflight
```

Preflight checks:

- LLM provider selection
- required model name
- required API key when applicable
- LLM server `/models` availability when a base URL is configured
- video provider support
- video service availability
- selected workflow discovery and callability
- workflow directory existence
- visual observer provider selection
- VLM model, base URL, API key, and server status where required

## Workflow Discovery

ShotForge expects API-format workflows for video generation. The workflow
discovery API returns:

- bundled workflows
- workflows found under the configured local directory
- warnings for missing folders or invalid workflow files
- `callable` status
- workflow id, source, format, node count, and path

Use:

```text
GET /api/comfyui/workflows?root=<workflow-directory>
```

## Configuration Order

For run creation, effective configuration is built in this order:

1. load default settings
2. load the default saved provider profile when available
3. build a profile from the Web/API payload
4. apply the profile in a scoped runtime context
5. record provider metadata into `ProjectState.metadata`

This makes each run reproducible from its saved package and profile metadata.
