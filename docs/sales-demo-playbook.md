# Sales Demo Playbook

This playbook turns ShotForge from a developer demo into a solution-architect demo for customer conversations.

## Demo Positioning

Use this sentence:

```text
ShotForge is not a one-shot video generator. It is an AI Agent Harness that turns a business creative goal into a traceable, evaluated, provider-ready production package.
```

## Audience

| Audience | What To Emphasize |
|---|---|
| Customer executive | Cost, speed, stability, reviewability, provider optionality |
| Product owner | End-to-end workflow, user handoff, review loop, POC scope |
| Technical architect | State, context, tools, MCP, sandbox, memory, provider surfaces |
| Creative lead | Storyboard, prompt package, visual targets, version diffs |

## 8-Minute Demo Flow

### 1. Business Problem

Start with a customer scenario:

```text
The team wants to create short-form campaign videos faster, but prompt-only workflows are hard to trace, evaluate, or hand off.
```

### 2. Input One Idea

Use a simple prompt:

```text
A quiet revenge reveal in a luxury elevator
```

Explain that the input is intentionally vague because the system must demonstrate structured planning, not just prompt expansion.

### 3. Show Generated Package

Show:

- storyboard
- shot list
- motion plan
- audio cues
- prompt package
- exports

Message:

```text
The vague goal is converted into a typed production package.
```

### 4. Show Provider Configuration

Show provider profile or preflight panel.

Message:

```text
The same workflow can run with mock providers for testing, local providers for private POC, and external providers for production.
```

### 5. Show Evaluation And Redesign

Show score, issues, correction plan, and prompt changes.

Message:

```text
The system does not rely on subjective feedback only. It converts quality gaps into structured issues and targeted corrections.
```

### 6. Show Harness Audit

Show:

- context sources
- tool orchestration
- agent contracts
- workflow decisions
- memory governance
- sandbox strategy
- MCP access

Message:

```text
This is the difference between a demo chain and a governable Agent Harness.
```

### 7. Show Delivery Readiness

Show readiness checks and next actions.

Message:

```text
The output includes what is ready, what is mocked, what needs a real provider, and what risks remain before pilot.
```

### 8. Close With Production Path

Close with:

```text
For a real customer, we keep the same state, policy, evaluation, and audit contracts. We replace mock providers with approved models, connect customer knowledge, and add deployment governance.
```

## Objection Handling

| Question | Answer |
|---|---|
| Is this just a video prompt demo? | No. The core asset is the Agent Harness: state, context, tools, memory, MCP, sandbox, evaluation, versioning, and export. |
| Why not call a video model directly? | Direct calls are hard to trace, evaluate, reproduce, and govern. ShotForge creates a controlled production loop before expensive generation. |
| Can this support our model provider? | Provider surfaces are separated into LLM/Judge, video generation, and visual observation. New adapters can be added without rewriting the workflow. |
| How do we measure value? | Time to package, generation waste reduction, visual target match, prompt coverage, review effort, and provider readiness. |
| What is not production-ready yet? | Auth, tenant isolation, official MCP transport, stronger sandbox isolation, production storage, and customer-specific knowledge overlays. |

## Demo Evidence Checklist

- Run package exists.
- Harness audit includes context/tool/contract/workflow/memory/sandbox/MCP evidence.
- Provider profile is visible.
- Evaluation report exists for full-loop demo.
- Prompt/version diff exists for redesign demo.
- Delivery readiness report lists risks and next actions.
- Exports are available for handoff.
