# Change Log

## 2026-05-31 Delivery Chain Consolidation

This milestone turns ShotForge from a concept scaffold into a runnable local delivery chain.

### Product Flow

- Added a FastAPI Web product shell with separate workflow and configuration pages.
- Added provider profile management for LLM/Judge, video generation, and visual observer settings.
- Added service preflight checks so missing local services, unreachable ComfyUI, missing workflows, and non-ready model endpoints are reported as actionable checks instead of raw server errors.
- Added a dedicated internal test chain button. The test provider remains available for deployment diagnostics but is no longer presented as the normal user path.
- Added run progress, recent run history, prompt-change display, generated artifact display, and readable per-iteration artifact folders.

### Real Local Provider Path

- Added local Ollama, vLLM, and OpenAI-compatible LLM provider support for evaluation and prompt redesign.
- Added ComfyUI provider execution with workflow discovery, local workflow selection, API-format validation, and video artifact resolution.
- Added bundled ComfyUI workflow support and readable generated artifact names.
- Added API and Web support for user-local ComfyUI workflows.

### Evaluation And Iteration

- Added layered evaluation structure from concrete visual facts to more abstract expression:
  - `physical_effect`
  - `frame_consistency`
  - `style_color`
  - `emotion_atmosphere`
  - `prompt_execution`
- Added physical target extraction from user ideas for subject count, required elements, location, weather, and action.
- Added prompt correction operations that write effect contracts, mandatory visible elements, and negative constraints into the actual generation prompt/template package.
- Added LLM evaluator JSON repair/fallback so a malformed judge response does not break the whole run.
- Added convergence metadata, prompt diffs, correction plans, version diffs, score deltas, and regression checks.

### Visual Observation Framework

- Added `shotforge.observation` with frame extraction, frame observers, sequence observation, and a `VideoObservationService`.
- Added visual observer providers:
  - `prompt-proxy`
  - `openai-vision`
  - `ollama-vision`
  - `vllm-vlm`
- Added `/api/observer-providers` and health metadata for observer configuration.
- Added VLM configuration fields across settings, provider profiles, API schemas, runtime environment application, preflight, Web forms, and run metadata.

### Application Architecture

- Split Web/API logic into shared application services:
  - `ProviderService`
  - `ProviderRuntimeService`
  - `ProviderPreflightService`
  - `ComfyUIWorkflowService`
  - `RunService`
  - `ArtifactService`
- Added structured package and observation schemas.
- Added extension-oriented infrastructure boundaries for MCP, sandbox, provider protocols, and generator clients.
- Added UI static asset structure for design tokens, reusable browser behavior, and future component/assets organization.

### Verification

- Current verification: `ruff check src tests` and `pytest -q`.
- Latest local result: `92 passed, 1 warning`.
