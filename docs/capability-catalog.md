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
- `playbooks`: reusable industry scenario assets.

Example:

```bash
curl http://127.0.0.1:8000/api/capabilities
```

CLI:

```bash
shotforge capabilities
```

The provider catalog intentionally includes unavailable planned providers. This helps explain model selection strategy while keeping the POC safe and local-first by default.
