# E-commerce Product Video Agent Solution

This solution package frames ShotForge for retail and e-commerce teams that need scalable product short-video production with consistent product facts and reviewable outputs.

## Customer Scenario

E-commerce teams need many product videos across SKUs, campaigns, and platforms. The key challenge is not only generating a video, but keeping product facts, required visual elements, style rules, and approval evidence consistent across iterations.

## Business Pain Points

| Pain Point | Business Impact | ShotForge Response |
|---|---|---|
| Product facts are scattered | Wrong claims or missing selling points | Knowledge base and structured prompt templates |
| Batch creative work is slow | Long cycle for SKU-level video variants | Agent workflow creates repeatable production packages |
| Output review is manual | Hard to detect missing product elements quickly | Physical target extraction and frame observation |
| Prompt changes are opaque | Teams cannot explain why a new version changed | Version diff and correction patch evidence |
| Provider selection is unclear | Cost and quality tradeoffs are hard to compare | Provider profiles and preflight strategy |

## Reference Agent Workflow

```text
Product goal
-> Product-oriented intent extraction
-> Product scene storyboard
-> Motion and camera plan
-> Prompt adapter with product constraints
-> Generation provider
-> Frame observation
-> Product element evaluation
-> Correction plan
-> Export package
```

## POC Scope

| Area | POC Boundary |
|---|---|
| Input | Product idea, selling point, style, platform, duration |
| Knowledge | Product facts, forbidden claims, style requirements |
| Output | Shot list, prompts, production package, evaluation report |
| Evaluation | Required product object, color, location, action, count |
| Review | Human-readable package and version diff |
| Integration | Export artifacts for downstream CMS or content workflow |

## Success Criteria

| Metric | Target | Evidence |
|---|---|---|
| Product fact coverage | Required product facts appear in prompt package | Prompt package and markdown brief |
| Visual element coverage | Required visible targets are checked | PhysicalEffectEvaluator and observation report |
| Batch repeatability | Same workflow can run for multiple product ideas | Run history and exported packages |
| Risk control | Forbidden claims and unsafe provider settings are visible | Context policy, delivery readiness, provider metadata |
| Handoff usability | Non-engineers can review CSV/Markdown exports | Export artifacts |

## Customer Value

- **Speed**: create SKU-level video plans faster than manual prompt drafting.
- **Quality**: evaluate whether product-specific visible elements are present.
- **Consistency**: reuse rubrics, prompt rules, and product knowledge assets.
- **Governance**: retain traceability for review and approval.

## Production Path

1. Add customer product catalog ingestion.
2. Add product compliance and forbidden-claim rules.
3. Configure provider profiles for draft and final generation.
4. Add batch run orchestration and artifact naming conventions.
5. Integrate package export with CMS or DAM systems.
6. Add approval roles and production storage.
