# Delivery Readiness

ShotForge generates a `DeliveryReadinessReport` for each design run.

The report is intentionally practical: it tells a reviewer what is ready for
handoff, which local provider configuration is still incomplete, and what needs
to be hardened before production use.

## Readiness Gates

Current gates include:

- `state_schema`: whether intent, shots, prompts, and versioned state exist.
- `context_observability`: whether agent context snapshots were recorded.
- `tool_policy`: whether tool calls have status and permission scope.
- `state_transition_audit`: whether state transitions and invariant checks were recorded.
- `context_safety`: whether context digests and redaction metadata are present.
- `mcp_capability`: whether required MCP-like tools are exposed.
- `memory_strategy`: whether reusable memory is available or should be seeded/promoted.
- `solution_architecture`: whether the run has an architecture summary.
- `export_contract`: whether JSON/CSV/Markdown export skills are registered.
- `provider_strategy`: whether the run has a real provider profile or only a local test profile.
- `evaluation_loop`: whether evaluation, redesign, or verification evidence exists.

These gates are intentionally broader than file export checks. They evaluate whether the Agent Harness can explain its context, tools, state transitions, MCP surface, memory strategy, and model/provider boundary.

## Handoff Deliverables

A normal run can produce:

- ProjectState JSON package
- Storyboard CSV package
- Markdown production brief
- Harness Inspector trace
- Run architecture summary
- Delivery readiness report

Planning/full-loop runs can additionally include:

- evaluation report and issue list
- correction plans and patches
- version diff and redesign evidence
- verification report

## How To Inspect

Through Web:

```text
http://127.0.0.1:8000/?run_id={run_id}
```

Through API:

```text
GET /api/runs/{run_id}/harness
GET /api/runs/{run_id}/readiness
```

Through CLI:

```bash
shotforge audit data/runs/{run_id}/package.json
```

## Production Boundary

This report does not claim the prototype is production-ready. It makes readiness explicit:

- local test provider means real provider credentials and service readiness are still required
- local file storage means production persistence is still required
- local sandbox policy means container isolation is still required
- static knowledge rules mean deployment-specific knowledge overlays are still required
