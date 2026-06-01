# Knowledge Assets

ShotForge should be reviewed as both a running POC and a reusable knowledge asset set. This document maps the reusable assets to customer solution work.

## Asset Map

| Asset | Location | Purpose |
|---|---|---|
| Industry playbooks | `src/shotforge/knowledge/industry_solution_playbooks.json` | Scenario patterns, value levers, risks, integrations |
| Evaluation rubrics | `src/shotforge/knowledge/evaluation_rubrics.json` | Quality dimensions and scoring structure |
| Prompt rules | `src/shotforge/knowledge/prompt_rules.json` | Prompt adaptation and provider-readiness patterns |
| Motion templates | `src/shotforge/knowledge/motion_templates.json` | Camera/motion guidance |
| Audio patterns | `src/shotforge/knowledge/audio_patterns.json` | Music and sound design cues |
| Correction strategies | `src/shotforge/knowledge/correction_strategies.json` | Routing from issues to correction agents |
| Solution docs | `docs/solutions/` | Customer-facing industry solution packages |
| POC strategy | `docs/poc-test-strategy.md` | POC test gates and acceptance criteria |
| Model matrix | `docs/model-selection-matrix.md` | Provider selection and tradeoff framework |
| Demo playbook | `docs/sales-demo-playbook.md` | Sales/solution-architect demo narrative |

## Reusable Best Practices

### Agent Harness

- Treat state as a typed contract.
- Record every context source and digest.
- Make tool calls policy-aware and auditable.
- Validate agent input/output contracts.
- Keep workflow decisions explicit.
- Separate provider selection from business workflow.
- Preserve version diffs and run summaries.

### Evaluation

- Start with physical target checks before subjective quality.
- Attach evidence to every issue.
- Route issues to targeted correction agents.
- Use score deltas and regression checks across versions.
- Keep mock/static evaluators for deterministic CI.
- Add LLM/VLM evaluators only when provider configuration is ready.

### Customer POC

- Keep POC scope narrow and measurable.
- Define success criteria before provider benchmarking.
- Use cheap loops before expensive generation.
- Record what is mocked, planned, and production-ready.
- Export artifacts that both technical and business reviewers can inspect.

## Knowledge Asset Roadmap

| Next Asset | Why It Matters |
|---|---|
| Customer discovery questionnaire | Helps identify high-value Agent scenarios |
| RFP / tender response template | Maps system capabilities to enterprise buying criteria |
| Cost model worksheet | Converts provider usage into budget estimates |
| Security review checklist | Makes sandbox, MCP, memory, and provider boundaries reviewable |
| Industry-specific rubric overlays | Turns generic evaluation into customer-specific success standards |
| Pilot rollout checklist | Bridges POC success to production deployment |

## How To Use In A Customer Conversation

1. Pick one industry solution package.
2. Use the POC test strategy to define scope and acceptance criteria.
3. Use the model selection matrix to choose provider candidates.
4. Run the demo playbook.
5. Export run package and delivery readiness report.
6. Convert open risks into the pilot rollout plan.
