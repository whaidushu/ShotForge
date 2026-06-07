# Industry Solution Playbooks

ShotForge includes packaged industry playbooks under:

```text
src/shotforge/knowledge/industry_solution_playbooks.json
```

These playbooks are lightweight knowledge assets used by the `solution_architect_agent`. They keep solution design from becoming hard-coded prose inside one agent.

## Current Playbooks

| Playbook | Scenario |
|---|---|
| `media_advertising_video_ops` | Campaign concept, brand-safe video planning, provider comparison |
| `gaming_character_content` | Character trailer ideation, NPC behavior video prompts, game asset motion references |
| `ecommerce_product_video` | SKU-to-video planning, promotion variants, platform-specific adaptation |
| `financial_service_explainer` | Explainer videos, risk education, governed onboarding content |

## What A Playbook Contains

Each playbook defines:

- industries
- scenario patterns
- value levers
- required integrations
- risk controls
- evaluation metrics

The generated `SolutionArchitecture` records which playbook was used through:

- `knowledge_assets`
- `scenario_patterns`
- `evaluation_metrics`
- `metadata.playbook_id`

## Why This Matters

For a solution architect role, the reusable asset is not only code. The reusable asset is the ability to package scenario knowledge into repeatable delivery patterns:

- how the customer scenario is framed
- which integrations are likely required
- which risks need review
- which metrics indicate value
- which POC criteria decide whether the solution should move to pilot

ShotForge keeps this layer explicit so it can later be replaced by customer-specific playbooks, RAG retrieval, or MCP-provided knowledge.
