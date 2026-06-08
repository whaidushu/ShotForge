# Evaluation Layers

ShotForge evaluates generated video from concrete facts toward abstract quality
signals. The first goal is not style polish. The first goal is to check whether
the requested visible elements actually appear.

## Layer Model

```text
L1 Physical facts
-> L2 Frame and sequence consistency
-> L3 Style and color
-> L4 Emotion and atmosphere
-> L5 Delivery readiness
```

## L1 Physical Facts

The physical layer extracts hard targets from the user idea:

- subject count
- required objects
- location
- weather or time
- visible action
- color or material constraints

Example:

```text
A cyber cat chases a glowing drone across rainy Shanghai rooftops
```

Expected physical targets include:

- cyber cat
- glowing drone
- rainy night
- Shanghai
- rooftop
- chasing action

The evaluation report records required, observed, and missing elements. The
correction plan should prioritize missing elements before adding more style text.

## L2 Consistency

Consistency checks whether important entities and actions remain stable across
frames:

- the same subject should not become a different subject
- faces or identity anchors should remain consistent
- key objects should remain present
- the action should continue instead of drifting into unrelated motion

## L3 Style And Color

Style/color evaluation checks whether the output follows requested visual
language after the physical layer is reasonably satisfied:

- palette
- lighting
- camera mood
- material feel
- genre style

## L4 Emotion And Atmosphere

This layer is intentionally more abstract. It should be evaluated only after
physical facts and consistency are not obviously broken.

Signals include:

- tension
- calmness
- urgency
- cinematic mood
- narrative emphasis

## Observation Pipeline

```text
video artifact
-> frame extraction
-> frame observer
-> sequence observation
-> evaluator context
-> evaluation report
-> correction plan
```

Observers can be local fallbacks or VLM providers. Real visual checks require a
configured VLM observer.

## Design Rule

Do not let prompt iteration become vague style expansion. The loop should first
identify missing visible facts, then write targeted constraints back into the
next prompt/template package.
