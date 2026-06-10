# API Reference

ShotForge exposes a local FastAPI API under `/api`. Start the Web app before
calling the endpoints:

```powershell
shotforge web --reload
```

The default local URL is:

```text
http://127.0.0.1:8000
```

## Request Conventions

- JSON requests use `Content-Type: application/json`.
- `run_id` is the folder name under `data/runs/{run_id}`.
- Most read endpoints return `404` when the run package or requested artifact is missing.
- Provider and generation failures are returned as `503` with a structured `detail`
  object containing readiness-style checks when possible.

## Health

### `GET /api/health`

Returns application and storage status. Use it to confirm the server can load
settings and resolve the configured storage paths.

Key response fields:

| Field | Meaning |
| --- | --- |
| `status` | Usually `ok` when the app is running. |
| `storage.storage_root` | Base storage directory. |
| `storage.runs_dir_exists` | Whether run storage exists. |
| `storage.versions_dir_exists` | Whether version storage exists. |
| `comfyui.*` | Current video-service settings. |
| `observer.*` | Current visual observer settings. |

### `GET /api/capabilities`

Returns the capability catalog: available agents, generator providers, LLM
providers, API routes, export formats, and registered playbooks.

Use this endpoint before building a UI around provider or export options.

## Effect Demos

### `GET /api/effect-demos`

Lists packaged effect-demo cases. Each item includes `case_id`, title,
duration, and local case path.

### `POST /api/effect-demos/{case_id}`

Runs a fixed v1/v2/v3 effect-demo case. v1 uses the raw user prompt, v2 applies
a translated structured prompt, and v3 is a candidate compensation pass after
frame observation. The comparison report records preservation locks and whether
the v3 candidate was accepted or rejected.

Request body:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `language` | string | `en` | Output language, `en` or `zh`. |
| `generator_provider_id` | string | `mock` | Generator provider used for all generated iterations. |
| `style` | string/null | null | Optional style override. |

Key response fields:

| Field | Meaning |
| --- | --- |
| `run_id` | Created run id. |
| `case_id` | Effect case id. |
| `comparison` | v1/v2/v3 score deltas, target changes, repaired/unresolved/regressed targets, preservation locks, candidate status, accepted iteration, and revision plan. |
| `exports` | Standard run export paths. |
| `state` | Full `ProjectState`. |

### `GET /api/runs/{run_id}/effect-comparison`

Returns the effect comparison report for a completed effect-demo run.

### `GET /api/effect-demos/{run_id}/comparison`

Alias for loading the comparison report from the effect-demo API namespace.

## Create A Run

### `POST /api/runs`

Creates a run and writes exports under `data/runs/{run_id}`.

Minimal design-only request:

```http
POST /api/runs
Content-Type: application/json

{
  "idea": "A neon train crossing a desert at sunrise",
  "style": "cinematic",
  "language": "en",
  "duration_seconds": 24
}
```

Full-loop request with evaluation:

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
  "provider_profile_name": "Local profile",
  "generator_provider_id": "<video-provider-id>",
  "llm_provider_id": "<llm-provider-id>",
  "llm_model": "<model-name>",
  "llm_base_url": "<openai-compatible-base-url>",
  "observer_provider_id": "<observer-provider-id>"
}
```

Planning request with iterative redesign:

```json
{
  "idea": "A product reveal shot in a rainy city street",
  "language": "en",
  "with_evaluation": true,
  "with_planning": true,
  "max_iterations": 3
}
```

### Run Request Fields

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `idea` | string | required | User idea, minimum 2 characters. |
| `style` | string | `cinematic` | Visual style hint used by the design pipeline. |
| `language` | `en` or `zh` | `zh` | Controls generated labels and natural-language output. |
| `duration_seconds` | integer | `24` | Range: 6-180. |
| `with_evaluation` | boolean | `false` | Runs generation and evaluation instead of design only. |
| `with_planning` | boolean | `false` | Runs iterative redesign after evaluation. |
| `rubric_id` | string | `baseline_v1` | Evaluation rubric id. |
| `max_iterations` | integer | `3` | Range: 2-10; used when planning is enabled. |
| `provider_profile_id` | string | profile id | Saved profile identifier. |
| `provider_profile_name` | string | profile name | Human-readable profile name. |
| `generator_provider_id` | string | provider id | Video provider id from the provider catalog. |
| `llm_provider_id` | string/null | profile value | LLM/Judge provider id. |
| `llm_model` | string/null | profile value | Model name for the selected LLM provider. |
| `llm_base_url` | string/null | profile value | Base URL for API-compatible providers. |
| `llm_api_key` | string/null | empty | Optional credential; not returned by profile APIs. |
| `evaluator_mode` | string/null | profile value | `mock`, `llm`, or `hybrid`. |
| `comfyui_base_url` | string/null | profile value | Video service base URL for ComfyUI-backed runs. |
| `comfyui_workflows_dir` | string/null | profile value | Local workflow search directory. |
| `comfyui_workflow_id` | string/null | profile value | Selected workflow id. |
| `comfyui_width` | integer/null | profile value | Range: 64-2048. |
| `comfyui_height` | integer/null | profile value | Range: 64-2048. |
| `comfyui_length` | integer/null | profile value | Range: 1-512 frames or provider-specific length unit. |
| `comfyui_fps` | number/null | profile value | Range: 1-60. |
| `comfyui_max_shots` | integer/null | profile value | Range: 0-32; `0` means no explicit shot cap. |
| `observer_provider_id` | string/null | profile value | Visual observer provider id. |
| `vlm_model` | string/null | profile value | Vision model name. |
| `vlm_base_url` | string/null | profile value | Base URL for local or API-compatible VLMs. |
| `vlm_api_key` | string/null | empty | Optional credential; not returned by profile APIs. |
| `vlm_frame_sample_count` | integer/null | `4` | Range: 1-16. |
| `vlm_confidence_threshold` | number/null | `0.65` | Range: 0-1. |
| `vlm_require_json` | boolean/null | `true` | Ask observer providers to return JSON when supported. |

### Run Response

`POST /api/runs` returns:

| Field | Meaning |
| --- | --- |
| `project_id` | Stable project id for version snapshots. |
| `run_id` | Local run folder id. |
| `version` | Current run version. |
| `exports` | Mapping of export format to local file path. |
| `state` | Full `ProjectState` payload. |

## Run Queries

### `GET /api/runs?limit=20`

Returns recent runs from `data/runs`. Each item includes run id, idea, mode,
provider profile, latest score, version, and update timestamp.

### `GET /api/runs/dashboard?limit=40`

Returns aggregate workbench status:

- total runs
- ready / needs revision / blocked counts
- average readiness score
- run summaries with lifecycle stage, score, issue count, artifacts, exports, and blockers

### `GET /api/runs/{run_id}`

Returns the full `ProjectState` for a run.

### `GET /api/runs/{run_id}/package-view`

Returns a grouped package view:

- `design`
- `generation`
- `observation`
- `evaluation`
- `iteration`
- `runtime`

Use this when the full state is too flat for a UI.

### `GET /api/runs/{run_id}/status`

Returns job status and progress steps. Missing runs return `404`.

### `GET /api/runs/{run_id}/trace`

Returns trace log entries from the run package.

### `GET /api/runs/{run_id}/runtime-evidence`

Returns runtime evidence such as context snapshots, tool calls, state
transitions, workflow decisions, policy records, and topology.

`GET /api/runs/{run_id}/harness` remains available as a compatibility alias.

### `GET /api/runs/{run_id}/workbench`

Returns the product-level workbench payload:

- summary
- lifecycle steps
- overview metrics
- iteration timeline
- handoff center
- runtime evidence summary
- next actions

### `GET /api/runs/{run_id}/generation-artifacts`

Returns generated artifact metadata. Each item includes provider, version,
iteration, shot id, local paths, and download URLs for video, prompt text,
prompt JSON, and workflow payload.

### `GET /api/runs/{run_id}/artifacts/{artifact_kind}/{iteration}/{shot_id}`

Downloads one generated artifact.

Allowed `artifact_kind` values:

- `video`
- `prompt`
- `prompt_json`
- `workflow`

Example:

```text
GET /api/runs/20260609_1420/artifacts/video/v001/shot_01
```

### `GET /api/runs/{run_id}/readiness`

Returns delivery readiness status, checks, summary counts, deliverables, next
actions, and risks. Returns `404` if no readiness report exists.

### `GET /api/runs/{run_id}/versions`

Returns saved version snapshots for the run's project id.

## Exports

### `GET /api/runs/{run_id}/export/{export_format}`

Downloads an export file. Supported values:

| Format | File |
| --- | --- |
| `json` | `package.json` |
| `package_view` | `package_view.json` |
| `csv` | `package.csv` |
| `markdown` or `md` | `package.md` |
| `manifest` | `manifest.json` |
| `trace` | `trace.json` |
| `run_summary` or `summary` | `run_summary.md` |
| `evaluation_csv` or `evaluation` | `evaluation.csv` |

Unsupported formats return `400`; missing files return `404`.

## Provider APIs

### `GET /api/provider-profiles`

Returns saved provider profiles, the default profile, and the profile storage
path. API keys are redacted and represented as `has_llm_api_key` or
`has_vlm_api_key`.

### `POST /api/provider-profiles`

Creates or updates a provider profile.

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
  "comfyui_fps": 8,
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

### `POST /api/preflight`

Runs readiness checks for a provider profile-shaped payload. Response fields:

| Field | Meaning |
| --- | --- |
| `status` | `passed`, `warning`, or `failed`. |
| `failed` | Number of failed checks. |
| `warnings` | Number of warning checks. |
| `checks` | List of `{check_id, label, status, detail}`. |
| `profile` | Public profile payload with secrets redacted. |

### `GET /api/observer-providers`

Returns visual observer provider descriptors and the default profile.

### `GET /api/comfyui/workflows?root=<path>`

Discovers API-format workflows from the configured workflow roots and optional
`root` query parameter. Response fields include:

- `enabled`
- `base_url`
- `workflow_id`
- `workflows_dir`
- `workflows`
- `warnings`

### `POST /api/test-chain`

Runs the built-in local test chain. This is intended for installation sanity
checks and does not replace real provider preflight.

## CLI Reference

| Command | Purpose |
| --- | --- |
| `shotforge design "idea"` | Build storyboard, prompt package, and exports. |
| `shotforge full-loop "idea"` | Run design, generation, evaluation, readiness, and exports. |
| `shotforge full-loop "idea" --redesign --max-iterations 3` | Add iterative redesign after evaluation. |
| `shotforge evaluate data/runs/{run_id}/package.json` | Evaluate an existing package. |
| `shotforge inspect data/runs/{run_id}/package.json` | Print a package summary. |
| `shotforge audit data/runs/{run_id}/package.json` | Print runtime evidence. |
| `shotforge capabilities` | Print provider, agent, route, and export capabilities. |
| `shotforge comfyui-workflows --root <path>` | List workflow files and callability. |
| `shotforge doctor --deep` | Check storage and provider readiness. |
| `shotforge web --reload` | Start the local Web app. |
