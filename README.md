# ShotForge_BD

**Industry-grade AI Agent Harness for evaluation-driven video creative workflows.**

ShotForge_BD is a solution-demo branch of ShotForge. It uses an AI video creative workflow as the business scenario, but the main focus is the Agent Harness itself: context engineering, tool orchestration, state management, evaluation, redesign, versioning, MCP/Sandbox/Memory extension points, and a clear path from POC to production.

中文定位：**面向 AI 视频创作场景的行业级 Agent Harness 解决方案样板**。

## What It Demonstrates

ShotForge_BD turns a vague creative idea into a structured, traceable, and iteratively improved video production package.

```text
User Idea
  -> Context Engineering
  -> LangGraph Agent Workflow
  -> Structured ProjectState
  -> Mock Generation
  -> Layered Evaluation
  -> Redesign / Correction
  -> VersionDiff / RegressionCheck
  -> JSON / CSV / Markdown Export
```

The project is intentionally provider-neutral. Mock providers keep the loop cheap and deterministic; real LLM / video / MCP / sandbox providers can be attached behind stable interfaces.

## Core Capabilities

| Capability | Implementation |
| --- | --- |
| Agent Harness Runtime | `AgentHarnessRuntime` wraps each Agent execution and records context, tools, policy, MCP and sandbox metadata |
| Context Engineering | `ContextBundle`, `ContextSource`, `ContextWindowPolicy` organize context by source, priority and budget |
| Tool Orchestration | `SkillRegistry`, `SkillSpec`, `ToolCallRecord` track tool schema, permission scope, risk and latency |
| State Management | `ProjectState` is the single state object across design, generation, evaluation, redesign and export |
| Evaluation System | Layered rubric, evaluator signals, score card, issue list and regression checks |
| Redesign Loop | Suggestion, correction routing, specialized correction agents and output structuring |
| Versioning | Snapshot, version chain, field-level `VersionDiff` and convergence status |
| Agent Infra | Mock MCP client, local sandbox policy, in-memory store and provider extension points |
| Web Demo | Harness Inspector shows Context, Tools, State, Policy, MCP, Sandbox and Memory runtime records |

## Why This Is Not Just a Video Generator

Most video tools optimize the next generation call. ShotForge_BD optimizes the production process around that call:

- **Business goal:** reduce creative trial-and-error cost.
- **Engineering goal:** make each Agent step observable, controllable and replaceable.
- **Quality goal:** turn "not good enough" into scored issues, suspected causes and targeted corrections.
- **Delivery goal:** export a production package that can be inspected, versioned and handed to downstream tools.

## Architecture

```text
app/
  cli/ web/ api/                 # Entry points

core/
  project_state.py               # Typed state model
  harness_runtime.py             # Agent runtime wrapper
  context_builder.py             # Context engineering
  execution_policy.py            # Runtime policy
  tool_call.py                   # Tool call records
  memory.py                      # Memory interface
  version_manager.py             # Snapshot and fork
  convergence_engine.py          # Iteration stop conditions

agents/
  design/                        # Intent, storyboard, motion, audio, prompt
  evaluation/                    # Verification, evaluation, suggestion, routing
  correction/                    # Specialized correction agents
  structuring/                   # Patch -> next ProjectState
  export/                        # Package export

infra/
  mcp/                           # Mock MCP client contract
  sandbox/                       # Local sandbox policy and dry-run runner
  skills/                        # Skill protocol exports

generators/
  mock_generator.py              # Deterministic development generator
  comfyui_provider.py            # ComfyUI exploration provider
  kling_provider.py              # Planned provider
  jimeng_provider.py             # Planned provider
  runway_provider.py             # Planned provider

evaluators/
  mock_visual_evaluator.py
  prompt_static_evaluator.py

knowledge/
  evaluation_rubrics.json
  correction_strategies.json
  prompt_rules.json
```

## Web Demo

```powershell
cd C:\Users\whaid\OneDrive\Project\ShotForge_BD
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn shotforge.app.web.app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Recommended demo mode:

```text
Run mode: Design + Evaluation + Redesign V2
Generator provider: Mock Generator
Max redesign iterations: 3
```

After running, inspect:

- Evaluation score and issue list
- Correction plans and patches
- Version chain and field-level diff
- Convergence check
- Harness Inspector: Context, Tool Calls, State, Policy, MCP, Sandbox, Memory

## CLI

```powershell
shotforge design "A quiet revenge reveal in a luxury elevator" --language en
shotforge full-loop "A quiet revenge reveal in a luxury elevator" --language en --redesign --max-iterations 3
```

## API

```http
POST /api/runs
Content-Type: application/json

{
  "idea": "A quiet revenge reveal in a luxury elevator",
  "style": "cinematic",
  "language": "en",
  "duration_seconds": 24,
  "with_planning": true,
  "max_iterations": 3,
  "generator_provider_id": "mock"
}
```

Exports:

```http
GET /api/runs/{run_id}/export/json
GET /api/runs/{run_id}/export/csv
GET /api/runs/{run_id}/export/markdown
GET /api/runs/{run_id}/export/evaluation_csv
GET /api/runs/{run_id}/trace
GET /api/runs/{run_id}/versions
```

## Solution Documents

- `docs/JD_ALIGNMENT.md`: capability matrix for the solution-demo branch
- `docs/AGENT_HARNESS_RUNTIME.md`: runtime design
- `docs/EVALUATION-LAYERS.md`: layered evaluation and convergence strategy
- `docs/STRUCTURED-PROMPT.md`: structured prompt template design
- `docs/ARCHITECTURE.md`: detailed architecture notes
- `docs/PRODUCT-DESIGN-NOTES.md`: product thinking notes

## Development Check

```powershell
python -m ruff check src tests
python -m pytest
python -m compileall -q src
```

## Current Scope

This branch keeps ComfyUI as an exploration provider. The mainline demo remains mock-first so that the Agent Harness, evaluation loop and runtime observability are deterministic and cheap to run.
