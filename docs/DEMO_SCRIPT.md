# ShotForge_BD Demo Script

Goal: show an end-to-end Agent Harness solution in 5-8 minutes.

## 1. Positioning

ShotForge_BD is not a one-shot video generator. It is an Agent Harness solution demo for turning vague creative goals into evaluated, traceable and iteratively improved production packages.

Key line:

> The video workflow is the scenario; the reusable capability is the production-grade Agent Harness.

## 2. Run The Demo

Open the Web app:

```powershell
uvicorn shotforge.app.web.app:app --reload
```

Use:

```text
Idea: A quiet revenge reveal in a luxury elevator
Language: English
Run mode: Design + Evaluation + Redesign V2
Generator provider: Mock Generator
Max redesign iterations: 3
```

## 3. Explain The Result

Walk through these sections in order:

1. **Evaluation**
   - Show overall score, dimensions and issue list.
   - Explain that vague dissatisfaction becomes structured issues.

2. **Harness Inspector**
   - Context: which context sources entered the Agent runtime.
   - Tool Calls: which skills were called and their latency.
   - State: current version, trace events, evaluation count and correction count.
   - Policy: execution constraints are explicit.
   - MCP/Sandbox/Memory: extension points are visible even in mock mode.

3. **Correction Plans / Patches**
   - Show the selected correction agent and affected fields.
   - Explain targeted correction instead of rewriting the whole prompt.

4. **Version Chain**
   - Show before/after field diff.
   - Explain traceability and regression control.

5. **Exports**
   - JSON for system integration.
   - CSV for production planning.
   - Markdown for human review.

## 4. Technical Takeaways

- LangGraph handles workflow orchestration.
- `AgentHarnessRuntime` handles production concerns around each Agent.
- `ProjectState` is the typed state contract.
- `ContextBundle` makes context engineering inspectable.
- `SkillRegistry` makes tool calls traceable.
- `EvaluationReport` and `VersionDiff` make quality and change measurable.

## 5. Production Extension Story

For a real customer:

- Swap mock LLM with an enterprise LLM provider.
- Connect customer knowledge through MCP / RAG.
- Add visual evaluators for real generated assets.
- Enforce sandbox and execution policies.
- Persist traces and memory in production stores.
- Keep the same Agent Harness contract.
