# Project Spine And Demo Path

This document is the short version of how ShotForge should be understood and reviewed.

## One Sentence

ShotForge is an AI video Agent Workbench that explores how an agent runtime, evaluation loop, and workflow version management can turn one vague creative idea into a traceable, auditable, versioned, and handoff-ready production package.

## Architecture Spine

```text
User Idea
  -> LangGraph Agent Workflow
  -> ProjectState
  -> Context Engineering
  -> Tool Orchestration
  -> Solution Architecture
  -> Delivery Readiness
  -> Version Diff / Run History
  -> Exports
  -> Harness Audit
```

The core is not the video prompt itself. The core is the runtime contract around the prompt:

- `ProjectState`: one typed state object across agents, evaluation, readiness, exports, and audit.
- `AgentCatalog`: agent roles, inputs, outputs, dependencies, skills, and extension points.
- `ContextBuilder`: ranked, budgeted, redacted, digestable context packs.
- `SkillRegistry`: governed tool execution with permission scope, risk level, call budget, and audit records.
- `AgentHarnessRuntime`: context snapshots, tool records, state transitions, policies, MCP, sandbox, and memory evidence.
- `VersionManager` / `VersionDiffBuilder`: snapshots, forks, field-level changes, prompt diffs, issue deltas, and run history.
- `LocalMCPAdapter`: MCP-like tool/resource discovery for knowledge, run packages, and harness audit.
- `LocalSandboxRunner`: local policy gate with execution profiles and structured denial records.
- `LocalMemoryStore`: namespaced, ranked, access-tracked memory with run promotion.
- `DeliveryReadinessReport`: POC gates and handoff next actions.

## What To Review

The demo should not present ShotForge as an already polished video product.

It should make these points inspectable:

1. A vague idea becomes structured state.
2. Every agent step is inspectable.
3. Context is engineered, not blindly concatenated.
4. Tools are governed, not just called.
5. State changes are tracked across the graph.
6. MCP/Sandbox/Memory are real extension boundaries.
7. Version diffs and run history explain what changed between iterations.
8. The run produces handoff artifacts, not just screen output.
9. The system can explain what is ready, diagnostic-only, and still required before pilot.

## Primary Demo Path

Use this path when showing the project quickly.

```powershell
.\scripts\demo.ps1 -Language en
```

This generates a run and immediately prints `shotforge audit`.

Show these outputs in order:

1. `run_summary.md`
   - Use it as the customer-facing summary.
   - Point out solution, readiness, and run evidence.

2. `manifest.json`
   - Use it as the integration handoff manifest.
   - Point out deliverables, readiness, and API links.

3. `trace.json`
   - Use it as the technical audit artifact.
   - Point out trace logs, context snapshots, tool calls, transitions, topology.

4. `shotforge audit data/runs/{run_id}/package.json`
   - Use it as the terminal inspection path.
   - Point out agent roles, MCP tools, state transitions, and invariant status.

5. Web Demo
   - Use it for visual inspection after the CLI path is clear.
   - Show Harness Inspector, Agent Topology, Delivery Readiness, version chain, artifacts, and exports.

## Web Demo Path

Start:

```powershell
python -m uvicorn shotforge.app.web.app:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Recommended settings:

- Language: English
- Mode: Design + Evaluation + Redesign V2
- Generator provider: Mock Generator
- Max redesign iterations: 3

Walkthrough order:

1. Generated storyboard and prompts.
2. Solution Architecture.
3. Delivery Readiness.
4. Harness Inspector.
5. State Transitions and Agent Topology.
6. Evaluation and correction loop.
7. Version chain and exports.

## API Demo Path

Useful endpoints:

```text
GET /api/health
GET /api/capabilities
POST /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/harness
GET /api/runs/{run_id}/readiness
GET /api/runs/{run_id}/export/{format}
```

The most important endpoint is:

```text
GET /api/runs/{run_id}/harness
```

It is the clearest inspection path for the Agent Harness runtime, not only the generated prompt package.

## What To Avoid In The Demo

Avoid leading with:

- UI polish.
- Electron packaging.
- Real video generation.
- Open-ended product vision.
- Too many docs.

Those are valid later, but they distract from the current strongest asset: the Agent Harness and versioned iteration workflow.

## Current Boundary

ShotForge is still a local-first POC.

Implemented:

- mock LLM and mock generator path
- local LLM / VLM / ComfyUI provider configuration paths
- typed state
- multi-agent workflow
- context/tool/state audit
- version snapshots and version diffs
- run history and artifact links
- MCP-like local adapter
- local sandbox policy
- local memory
- exports and readiness
- CLI/Web/API demo paths

Still future work:

- official MCP transport
- stronger sandbox isolation
- production storage
- auth and tenancy
- customer-specific RAG/playbook overlays
- production-grade background jobs, observability, and quota controls
- product-grade UI polish

## Recommended Next Planning Question

The next planning decision should be:

```text
Do we deepen the Agent Harness as an infra project,
or do we freeze the Harness baseline and start productizing the video workflow?
```

Both are valid, but they should not be mixed in the same sprint.
