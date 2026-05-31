# Capability Catalog API

ShotForge exposes a compact solution capability catalog:

```text
GET /api/capabilities
```

The catalog includes:

- agent specs and dependency edges
- Agent Harness components
- MCP/Sandbox/Memory/Knowledge Base capabilities
- generator provider catalog
- LLM provider catalog
- visual observer provider catalog
- packaged industry playbooks
- supported export formats
- main API routes

This endpoint is useful for solution walkthroughs because it shows what is implemented, what is available, and what is planned without requiring a source-code tour.

Important sections:

- `agents`: role, inputs, outputs, dependencies, skills, tags, and extension points.
- `agent_harness`: core runtime components.
- `infra`: MCP, sandbox, memory, and knowledge capabilities.
- `generator_providers`: available and planned video generation adapters.
- `llm_providers`: available and planned LLM adapters.
- `observer_providers`: prompt-proxy and VLM-backed frame observers exposed through `/api/observer-providers`.
- `playbooks`: reusable industry scenario assets.
- `api_routes`: run creation, package-view retrieval, run status, provider profiles, observer providers, ComfyUI workflow discovery, preflight, internal test chain, exports, and artifact download routes.

Example:

```bash
curl http://127.0.0.1:8000/api/capabilities
```

CLI:

```bash
shotforge capabilities
```

The provider catalog intentionally includes unavailable planned providers. User-facing provider selectors hide the internal test provider by default; `/api/test-chain` is the explicit deployment diagnostic path for exercising that provider.

Visual observer providers are intentionally separate from LLM and video providers. The LLM provider evaluates or rewrites text, the video provider renders MP4 artifacts, and the observer provider inspects frames so physical and consistency evaluators can compare the requested targets against visible output.
