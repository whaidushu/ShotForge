# Agent Infra Runtime

ShotForge includes a minimal Agent Infra runtime layer. The goal is to make agent execution visible, policy-aware, and extensible instead of leaving MCP, sandbox, memory, and skills as placeholder words.

This is a v0 implementation. It is intentionally local-first and testable.

## Components

| Component | Current Capability | Production Boundary | Evidence |
|---|---|---|---|
| Context Engineering | Each agent receives a built context from project state and knowledge sources | Replaceable retrieval and memory sources | `HarnessContextSnapshot` |
| Tool Orchestration | `SkillRegistry` records skill calls, latency, permission scope, tool plan, schema status, and fallback outcome | Replaceable tool registry and stricter permission policy | `ToolCallRecord`, `ToolOrchestrationRecord` |
| MCP Adapter | Local MCP-like tool/resource adapter exposes knowledge search and run package access | Official MCP transport can replace adapter | `LocalMCPAdapter` |
| Sandbox | Local command sandbox enforces command, timeout, cwd, workspace, network, env, file-write, and artifact policy | Docker/container isolation planned | `LocalSandboxRunner`, `SandboxPolicyRecord` |
| Memory | JSONL local memory store plus governance manager for selection, promotion, namespace, kind, and importance policy | Redis/SQLite/vector memory can replace store | `LocalMemoryStore`, `MemorySelectionRecord` |
| Runtime Policy | Execution and sandbox policy are captured per agent context | Policy can be customer/project specific | `ExecutionPolicy`, `SandboxPolicy` |
| Agent Catalog | Agents have explicit roles, IO contracts, dependencies, skills, tags, and extension points | Dynamic registry and marketplace-style agent loading can replace static catalog | `AgentSpec`, `AgentCatalog` |
| Agent Contracts | Runtime validates agent preconditions and postconditions around every known agent | Contract severity, repair strategy, and human approval can become customer policy | `AgentContractReport` |
| Workflow Routing | Runtime records route decisions such as continue, review, repair, block, and complete | LangGraph conditional edges can consume these decisions directly | `WorkflowDecisionRecord` |
| State Transitions | Runtime records before/after summaries, changed fields, and invariants for every agent | Stronger schema-level validation and rollback can be added | `StateTransitionRecord` |

## Runtime Flow

```text
Agent node starts
  -> AgentHarnessRuntime validates agent preconditions
  -> AgentHarnessRuntime builds ranked/budgeted context
  -> runtime records knowledge refs, memory hits, available skills, MCP tools, policies, agent spec
  -> agent handler runs
  -> runtime validates agent output contract
  -> SkillRegistry records tool calls
  -> runtime records state transition and invariants
  -> runtime records workflow routing decision
  -> ProjectState stores trace, context snapshot, tool calls, contracts, routing, and transitions
```

## Why This Matters

The target solution-architect scenario is not only about generating text or video. A customer-facing Agent solution must explain:

- What context was used.
- Which tools were available.
- Which tools were called.
- What safety policy constrained execution.
- Whether memory or knowledge sources influenced the answer.
- Whether each agent satisfied its input/output contract.
- What the harness recommended after each agent step.
- How the run can be audited after execution.

ShotForge stores this evidence in `ProjectState`:

- `harness_contexts`
- `tool_call_records`
- `tool_orchestration_records`
- `knowledge_refs`
- `memory_refs`
- `memory_selection_records`
- `sandbox_policy_records`
- `mcp_access_records`
- `trace_logs`
- `state_transitions`
- `agent_contract_reports`
- `workflow_decisions`

The same evidence is available through:

```text
GET /api/runs/{run_id}/harness
shotforge audit data/runs/{run_id}/package.json
```

This gives a reviewer a compact audit view without opening internal code.

## Agent Contract Strategy v1

`AgentContract` defines explicit runtime expectations for each known agent:

- required inputs, such as `creative_intent` before `storyboard_agent`
- required outputs, such as `shots.motion` after `motion_agent`
- cross-field conditions, such as audio cue count matching shot count
- blocking preconditions before an agent can run
- advisory postconditions that can trigger repair routing

This changes the main pipeline from a blind function chain into a governed execution path. If a downstream agent is invoked before upstream state exists, the runtime records a failed `AgentContractReport`, emits a `block` workflow decision, and raises before the agent mutates state.

## Workflow Decision Strategy v2

`WorkflowController` records an advisory decision after each agent:

- `continue` for the normal static route
- `review` when delivery readiness warns or fails
- `repair` when an agent output contract fails
- `block` when preconditions fail
- `complete` after export

The controller also attaches gate metadata:

- tool orchestration failures
- memory selection count
- sandbox policy record count
- MCP access record count
- observation report count
- export count

The current LangGraph path still runs as a deterministic POC flow, but these records are the strategy surface for the next step: conditional graph edges that consume routing decisions instead of hard-coded linear edges.

## MCP Strategy v1

`LocalMCPAdapter` supports server/tool/resource discovery:

- `knowledge.search`
- `runs.list`
- `runs.get_package`
- `runs.get_harness_audit`
- `list_resources`
- `read_resource("shotforge://runs/{run_id}/package")`
- `read_resource("shotforge://runs/{run_id}/harness")`
- `list_prompts`

The adapter now has `MCPAccessPolicy`:

- allowed tools
- allowed resource URI prefixes
- prompt exposure switch
- max run-list limit
- known-tool requirement

Every list/call/read operation records an `MCPAccessRecord`. This is still not a full official MCP server yet. It is a local adapter that maps ShotForge capabilities into tool/resource/prompt primitives. The next step is to add stdio or HTTP transport.

## Sandbox Strategy v1

`LocalSandboxRunner` supports:

- dry-run mode
- command allowlist
- working directory policy
- workspace boundary
- denied private/secret path fragments
- network access policy
- file-write policy
- timeout policy
- stdout/stderr capture
- execution profiles
- structured denied results
- artifact manifest capture

Every sandbox check records `SandboxPolicyRecord`, including profile, command, decision, network/write policy, env allowlist, and captured artifacts. This is a policy boundary, not container isolation. Docker-based isolation is the planned production boundary.

## Memory Strategy v1

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

`MemoryManager` adds governance around that store:

- allowed namespaces, including legacy `default` and runtime `shotforge`
- allowed memory kinds
- minimum importance
- max hits per agent
- explicit promotion agents
- readiness-aware promotion
- selection and promotion reasons

Runtime selection and promotion both produce `MemorySelectionRecord`. This gives the local POC a concrete cross-run learning path without requiring an external vector database.

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

## Tool Orchestration v3

`SkillRegistry` now acts as a lightweight tool orchestrator, not just a function registry. Each tool call can carry:

- `agent_name`
- `purpose`
- `expected_output`
- `fallback_tools`
- `tool_plan_id`

The registry records a `ToolOrchestrationRecord` for every planned call:

- requested tool
- selected tool
- attempted tools
- authorization decision and reasons
- schema status and schema issues
- fallback usage and outcome
- policy snapshot

The current schema validation is intentionally simple and local-first:

- input schema can require positional argument count
- input schema can require keyword names
- output schema can validate primitive return type

This is enough to demonstrate the harness strategy boundary without locking the POC into a specific external tool framework. Later production adapters can replace this with JSON Schema, Pydantic models, OpenAPI tool contracts, or MCP tool schemas.

Example behavior:

```text
primary tool planned
  -> policy authorization
  -> input schema validation
  -> tool execution
  -> output schema validation
  -> fallback if enabled and primary fails
  -> orchestration record stored in ProjectState
```

This gives the reviewer a concrete answer to "how are skills orchestrated?" instead of only seeing a list of callable functions.

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
