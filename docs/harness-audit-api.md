# Harness Audit API

ShotForge exposes run-level Agent Harness evidence through:

```text
GET /api/runs/{run_id}/harness
```

The response is designed for demo review, solution walkthroughs, and debugging. It includes:

- `contexts`: context snapshots produced for each agent.
- `tool_calls`: tool execution records from `SkillRegistry`.
- `state_transitions`: before/after state summaries and invariant status per agent.
- `agent_topology`: executed agent nodes and edges derived from the run.
- `policies`: execution policy, MCP tools, sandbox policy, and memory summary.
- `state_summary`: trace, knowledge, memory, evaluation, correction, and export counts.
- `solution`: industry scenario, playbook-backed knowledge assets, and POC criteria.
- `readiness`: delivery gates, next actions, handoff deliverables, and risks.

Example:

```bash
curl http://127.0.0.1:8000/api/runs/20260529_1509/harness
```

This endpoint is intentionally read-only. It is not a replacement for a full observability stack, but it makes the POC's state management, context engineering, tool orchestration, MCP/Sandbox/Memory hooks, and delivery readiness visible without opening the source code.
