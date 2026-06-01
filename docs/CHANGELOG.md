# Change Log

## 2026-06-01 Agent Harness Strategy And Solution Assets

This milestone deepens the Agent Harness strategy layer and adds customer-facing solution assets for solution-architect review.

### Harness Strategy

- Added memory governance around local JSONL memory:
  - namespace policy
  - allowed memory kinds
  - minimum importance
  - max hits per agent
  - promotion decisions and reasons
- Added workflow gate metadata for tool failures, memory, sandbox, MCP, observations, and exports.
- Added sandbox strategy records for workspace boundary, private path fragments, network policy, file-write policy, env allowlist, and artifact boundary.
- Added MCP access policy and records for tools, resources, prompts, access limits, and denied operations.
- Exposed memory, sandbox, and MCP evidence through harness audit and CLI audit.

### Solution Assets

- Added industry solution packages:
  - advertising video agent solution
  - e-commerce product video agent solution
  - game trailer and character video agent solution
- Added POC test strategy with phases, gates, cases, metrics, and production exit criteria.
- Added model selection matrix for LLM/Judge, video generation, and visual observation providers.
- Added sales demo playbook for customer-facing walkthroughs and objection handling.
- Added knowledge asset index for playbooks, rubrics, prompt rules, correction strategies, and solution templates.

### Verification

- Current verification: `ruff check src tests` and `pytest`.
- Latest local result: `95 passed`.

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
