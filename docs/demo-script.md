# Demo Script

This script is designed for a 5-8 minute walkthrough.

## 1. Positioning

ShotForge is not a one-shot video generator.

It is an Agent Harness solution demo for turning vague creative goals into evaluated, traceable, and iteratively improved production packages.

Key line:

```text
The video workflow is the scenario; the reusable capability is the production-grade Agent Harness.
```

## 2. Run The Demo

Start the Web app:

```powershell
uvicorn shotforge.app.web.app:app --reload
```

Suggested input:

```text
Idea: A quiet revenge reveal in a luxury elevator
Language: English
Run mode: Design + Evaluation + Redesign
Generator provider: Mock Generator
Max redesign iterations: 3
```

## 3. Walkthrough Order

1. **Generated Package**
   - Show storyboard, prompts, audio cues, and exports.
   - Explain that a vague idea becomes a structured production package.

2. **Evaluation**
   - Show score, dimensions, and issue list.
   - Explain that vague dissatisfaction becomes structured, correctable issues.

3. **Agent Infra Runtime**
   - Show context sources, tool calls, execution policy, MCP tools, sandbox policy, and memory hits.
   - Explain that this is the difference between a demo script and an inspectable Agent Harness.

4. **Correction Plans / Patches**
   - Show selected correction agent and affected fields.
   - Explain targeted correction instead of rewriting the entire prompt.

5. **Version Chain**
   - Show before/after diff.
   - Explain traceability, regression control, and convergence.

6. **Exports**
   - JSON for system integration.
   - CSV for production planning.
   - Markdown for human review.
   - Evaluation CSV for quality review.

## 4. Technical Takeaways

- LangGraph handles workflow orchestration.
- `ProjectState` is the typed state contract.
- `ContextBuilder` makes context engineering explicit.
- `SkillRegistry` makes tool calls traceable.
- `AgentHarnessRuntime` records runtime evidence.
- Evaluation and version diffs make quality and change measurable.

## 5. Production Extension Story

For a real customer:

1. Swap mock LLM with an enterprise provider.
2. Connect customer knowledge through RAG or MCP.
3. Add real generator providers.
4. Add visual/audio evaluators.
5. Enforce sandbox and execution policies.
6. Persist traces and memory in production stores.
7. Keep the same Agent Harness contract.
