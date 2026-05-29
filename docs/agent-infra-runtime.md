# Agent Infra Runtime

ShotForge includes a minimal Agent Infra runtime layer. The goal is to make agent execution visible, policy-aware, and extensible instead of leaving MCP, sandbox, memory, and skills as placeholder words.

This is a v0 implementation. It is intentionally local-first and testable.

## Components

| Component | Current Capability | Production Boundary | Evidence |
|---|---|---|---|
| Context Engineering | Each agent receives a built context from project state and knowledge sources | Replaceable retrieval and memory sources | `HarnessContextSnapshot` |
| Tool Orchestration | `SkillRegistry` records skill calls, latency, status, and permission scope | Replaceable tool registry and stricter permission policy | `ToolCallRecord` |
| MCP Adapter | Local MCP-like tool/resource adapter exposes knowledge search and run package access | Official MCP transport can replace adapter | `LocalMCPAdapter` |
| Sandbox | Local command sandbox enforces allowlist, timeout, cwd, and dry-run policy | Docker/container isolation planned | `LocalSandboxRunner` |
| Memory | JSONL local memory store supports cross-run searchable records | Redis/SQLite/vector memory can replace store | `LocalMemoryStore` |
| Runtime Policy | Execution and sandbox policy are captured per agent context | Policy can be customer/project specific | `ExecutionPolicy`, `SandboxPolicy` |
| Agent Catalog | Agents have explicit roles, IO contracts, dependencies, skills, tags, and extension points | Dynamic registry and marketplace-style agent loading can replace static catalog | `AgentSpec`, `AgentCatalog` |
| State Transitions | Runtime records before/after summaries, changed fields, and invariants for every agent | Stronger schema-level validation and rollback can be added | `StateTransitionRecord` |

## Runtime Flow

```text
Agent node starts
  -> AgentHarnessRuntime builds ranked/budgeted context
  -> runtime records knowledge refs, memory hits, available skills, MCP tools, policies, agent spec
  -> agent handler runs
  -> SkillRegistry records tool calls
  -> runtime records state transition and invariants
  -> ProjectState stores trace, context snapshot, tool call records, and transition records
```

## Why This Matters

The target solution-architect scenario is not only about generating text or video. A customer-facing Agent solution must explain:

- What context was used.
- Which tools were available.
- Which tools were called.
- What safety policy constrained execution.
- Whether memory or knowledge sources influenced the answer.
- How the run can be audited after execution.

ShotForge stores this evidence in `ProjectState`:

- `harness_contexts`
- `tool_call_records`
- `knowledge_refs`
- `memory_refs`
- `trace_logs`
- `state_transitions`

The same evidence is available through:

```text
GET /api/runs/{run_id}/harness
shotforge audit data/runs/{run_id}/package.json
```

This gives a reviewer a compact audit view without opening internal code.

## MCP v0

`LocalMCPAdapter` supports server/tool/resource discovery:

- `knowledge.search`
- `runs.list`
- `runs.get_package`
- `runs.get_harness_audit`
- `list_resources`
- `read_resource("shotforge://runs/{run_id}/package")`
- `read_resource("shotforge://runs/{run_id}/harness")`

This is not a full official MCP server yet. It is a local adapter that maps ShotForge capabilities into tool/resource primitives. The next step is to add stdio or HTTP transport.

## Sandbox v0

`LocalSandboxRunner` supports:

- dry-run mode
- command allowlist
- working directory policy
- timeout policy
- stdout/stderr capture
- execution profiles
- structured denied results
- artifact manifest capture

This is a policy boundary, not container isolation. Docker-based isolation is the planned production boundary.

## Memory v0

`LocalMemoryStore` stores JSONL records with:

- memory id
- kind
- content
- tags
- source run id
- metadata
- namespace
- importance
- access count
- last accessed timestamp

The runtime can search memory before an agent executes and record memory refs in the project state. Successful runs can also be promoted into reusable memory.

Runtime promotion currently captures completed run summaries after delivery readiness and before export, so exported packages include memory references. This gives the local POC a concrete cross-run learning path without requiring an external vector database.

## Context Engineering v2

`ContextBuilder` now produces structured context packs:

- ranked `ContextSource` records
- budget enforcement through `ContextBuildPolicy`
- prompt digest
- truncation metadata
- included and excluded source tracking
- basic redaction for token/secret-like values
- redacted source tracking

This makes the context supplied to each agent reproducible and reviewable.

## Tool Orchestration v2

`SkillRegistry` now has a `ToolExecutionPolicy`:

- allowed permission scopes
- max total calls
- max calls per tool
- high-risk approval policy

Denied tool calls are recorded as failed `ToolCallRecord` entries with authorization metadata.

## JD Alignment

This layer directly supports the JD keywords:

- Context Engineering
- Tool Orchestration
- State Management
- Skill
- MCP
- Agent Sandbox
- Memory
- Knowledge Base / RAG foundation
- Safety policy
- Stable engineering delivery from demo to production

## Tests

See:

```text
tests/test_agent_infra_runtime.py
```
