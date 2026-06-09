# Providers

ShotForge uses separate provider contracts for text reasoning, video rendering,
and visual observation. This keeps each service replaceable without changing the
core workflow state.

## Provider Roles

| Role | Responsibility | Main configuration |
| --- | --- | --- |
| LLM/Judge | prompt generation, prompt revision, LLM-based scoring | provider id, model, base URL, API key, evaluator mode |
| Video | render generated prompt packages into video artifacts | provider id, service URL, workflow id, render parameters |
| Visual Observer | inspect extracted frames and produce visual observations | provider id, model, base URL, API key, frame sampling |

## Generator Provider Contract

Generator providers implement the protocol in `src/shotforge/generators/base.py`:

| Method | Purpose |
| --- | --- |
| `generate(state)` | Render artifacts from `ProjectState`. |
| `supports_real_generation()` | Distinguish runnable providers from test/planned providers. |
| `estimate_cost(state)` | Return a cost estimate before invocation. |
| `capabilities()` | Describe modality, duration, aspect ratio, batch, and metadata support. |

`GeneratedResult` stores:

- provider id
- generation status
- generated shots
- artifact references
- observation report id
- provider metadata

Each `GeneratedShotResult` stores:

- `shot_id`
- `prompt_id`
- video URI/path
- duration
- detected elements
- motion/audio summaries
- quality signals
- frame observations
- artifact metadata

## Runnable Video Path

The currently runnable real video path is the ComfyUI-backed provider. It
requires:

- a reachable video service
- an API-format workflow
- a selected workflow id
- output nodes that produce files ShotForge can resolve
- render parameters compatible with the workflow

The provider writes per-shot assets such as:

- prompt text
- prompt JSON
- workflow API payload
- video artifact

These files are later exposed through `/api/runs/{run_id}/generation-artifacts`
and `/api/runs/{run_id}/artifacts/...`.

## Planned Or External Providers

The generator registry also contains planned provider adapters for common video
model integrations. Planned providers make the intended interface visible but do
not run unless their implementation and credentials are completed. Preflight
returns a failure when a selected provider is not runnable.

## LLM/Judge Providers

LLM/Judge providers are used by:

- design and prompt generation
- LLM-based storyboard/prompt scoring
- prompt redesign and correction

The provider profile stores the provider id, model name, base URL, and optional
API key. The evaluator mode controls how the evaluator registry is built:

| Mode | Behavior |
| --- | --- |
| `mock` | deterministic/test evaluators only |
| `llm` | LLM-based judge evaluator |
| `hybrid` | deterministic checks plus LLM judge |

## Visual Observer Providers

Visual observer providers inspect extracted frames and return structured
observations. The provider catalog exposes:

- `provider_id`
- display name
- provider type
- availability
- whether model/base URL/API key are required
- default hints
- description

Observation output is used by physical-effect and consistency evaluators to
compare actual frames with required targets.

## Prompt Proxy Observer

The prompt-proxy observer is a development fallback. It derives observations
from prompt/storyboard text rather than rendered pixels. It is useful for tests
and UI smoke checks, but real visual inspection requires a configured VLM
provider.

## Provider Preflight

Preflight checks one provider profile and returns a status:

- `passed`: all required services and workflow checks pass
- `warning`: the configuration is usable for limited paths but not fully real
- `failed`: a required service, provider, workflow, model, or credential is missing

Check records contain:

```json
{
  "check_id": "comfyui_workflow",
  "label": "ComfyUI workflow",
  "status": "passed",
  "detail": "<workflow-id> / api / 42 nodes"
}
```

## Adding A Provider

1. Implement the provider contract.
2. Register the provider in the relevant registry.
3. Add profile fields if the provider needs user configuration.
4. Add preflight checks for required services, credentials, models, or files.
5. Add tests for the provider contract and failure modes.
