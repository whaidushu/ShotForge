# Evaluation

ShotForge treats evaluation as an iterative workflow. The system checks whether
the generated artifact matches the user idea, identifies gaps, writes correction
plans, and preserves version evidence for comparison.

## Evaluation Pipeline

```text
ProjectState
-> generated video artifact
-> frame extraction
-> visual observation
-> evaluator registry
-> score card and issues
-> correction plan
-> prompt/template patch
-> regenerated version
-> score delta and regression check
```

## Layers

Evaluation starts from concrete visual facts and moves toward more abstract
creative qualities:

| Layer | What It Checks | Example Signals |
| --- | --- | --- |
| `physical_effect` | required visible facts | subject count, objects, color, location, weather, action |
| `frame_consistency` | stability across frames | element continuity, action continuity, identity stability |
| `style_color` | visual treatment | palette, lighting, style fit |
| `emotion_atmosphere` | expressive quality | mood, tension, atmosphere |
| `prompt_execution` | prompt/package quality | prompt coverage, constraints, correction adherence |

## Physical Targets

`src/shotforge/core/physical_targets.py` extracts concrete targets from the
user idea. Targets can include:

- primary subject
- required objects
- location and setting
- weather or atmosphere
- action
- explicit counts

These targets are converted into prompt constraints and evaluation expectations.
For example, if the idea requires a glowing drone, the physical-effect evaluator
can flag a generated artifact where no drone-like element is observed.

## Physical Convergence

`src/shotforge/core/physical_convergence.py` turns physical-effect evaluation
into target-level iteration evidence:

- target scores for required visible elements
- repair targets for missing or weak elements
- preservation locks for targets that are already visible
- candidate gates that accept or reject a regenerated version
- next revision focus when a candidate still misses or regresses targets

The built-in effect demo uses this module for its v1/v2/v3 comparison, and the
main redesign workflow uses the same module after ordinary full-loop evaluation.
This keeps demo cases separate from platform behavior: example-specific labels
and prompt patches stay in `examples/effect_cases`, while candidate acceptance
and regression checks stay in the core workflow layer.

## Observation

`VideoObservationService` runs after generation:

1. locate generated video files from shot metadata
2. extract sampled frames
3. call the configured frame observer
4. build shot observations
5. build sequence observations
6. attach observation reports to `ProjectState`

Observation records include frame path, detected elements, action summary,
identity summary, confidence, and metadata.

## Evaluator Registry

`EvaluatorRegistry.defaults()` registers evaluators based on settings:

- `PhysicalEffectEvaluator`
- `FrameConsistencyEvaluator`
- `MockVisualEvaluator` when mode is `mock` or `hybrid`
- `PromptStaticEvaluator` when mode is `mock` or `hybrid`
- `LLMStoryPromptEvaluator` when mode is `llm` or `hybrid`

## Scores And Issues

An `EvaluationReport` contains:

- `score_card.overall_score`
- dimension scores
- issues
- strengths
- suggested focus
- rubric id
- metadata

Each issue contains:

- severity: `low`, `medium`, `high`, or `critical`
- dimension id and label
- optional shot id
- description
- evidence
- suspected cause
- correction type

## Correction And Versioning

When issues are found, correction planning can create:

- `CorrectionPlan`
- `RedesignPlan`
- `CorrectionPatch`
- `CorrectionOperation`

Supported patch operations append or update targeted fields such as shot
description, motion, prompt text, negative prompt, structured template fields,
scene description, audio sound design, and character behavior.

After regeneration, ShotForge builds:

- `VersionDiff`
- `ScoreDelta`
- `RegressionCheck`
- `ConvergenceStep`

These records explain what changed, whether the score improved, which issues
were resolved, and whether new issues appeared.

For physical-effect redesigns, `RegressionCheck.metadata` and
`ConvergenceStep.metadata` also include a `physical_convergence_candidate_gate`.
If a candidate regresses a locked physical target or drops the target-level
score beyond tolerance, the candidate is marked as rejected and the accepted
version remains the source version in metadata.

## Rubrics

Rubrics are loaded through `RubricStore` and use typed configs:

- `EvaluationLayerConfig`
- `EvaluationDimensionConfig`
- `EvaluationIssueRule`
- `EvaluationRubric`

Dimensions define target descriptions, weights, layer mapping, signal keys,
hard-target flags, and issue thresholds.

## Practical Use

Use evaluation when you need to answer:

- Did required objects actually appear?
- Did the setting and action match the idea?
- Did objects or identities change across frames?
- Did the second generation improve the first?
- Which prompt constraints changed between versions?
- Which issues remain before export?
