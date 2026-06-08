# Runtime Audit API

ShotForge exposes run-level runtime evidence through:

```text
GET /api/runs/{run_id}/harness
```

The endpoint is read-only and is meant for debugging, review, and architecture
inspection. It complements the product-level workbench API.

The response includes:

- `contexts`: context snapshots produced for each agent.
- `tool_calls`: tool execution records from `SkillRegistry`.
- `state_transitions`: before/after state summaries and invariant status per agent.
- `agent_topology`: executed agent nodes and edges derived from the run.
- `policies`: execution policy, MCP-style tools, sandbox policy, and memory summary.
- `state_summary`: trace, knowledge, memory, evaluation, correction, generation,
  and export counts.
- `solution`: current run architecture metadata when present.
- `readiness`: delivery gates, next actions, handoff deliverables, and risks.

Example:

```bash
curl http://127.0.0.1:8000/api/runs/{run_id}/harness
```

Use this endpoint when you need to inspect how an idea moved through agents,
context construction, tool policy, provider boundaries, state transitions, and
export readiness without opening the source code.
