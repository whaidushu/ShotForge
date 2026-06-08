# Structured Prompt

ShotForge treats prompts as structured runtime artifacts, not only free-form
text. This makes prompts easier to evaluate, revise, version, and pass into video
providers such as ComfyUI.

## Why Structure Matters

Plain prompts are hard to inspect:

- required objects may be missing
- style and physical facts are mixed together
- correction agents cannot target one field safely
- version diffs are noisy

Structured prompt packages give the evaluation loop stable fields to read and
rewrite.

## Prompt Package Fields

The prompt package can contain:

- scene goal
- subject and object anchors
- action
- location
- time/weather
- camera and composition
- style and color
- motion constraints
- negative constraints
- physical effect contract
- provider-specific prompt
- provider-specific metadata

## Evaluation Mapping

| Prompt Area | Evaluation Use |
|---|---|
| subject/object anchors | physical target checks |
| action | motion and continuity checks |
| location/time/weather | scene correctness |
| style/color | style layer |
| negative constraints | artifact reduction |
| physical effect contract | missing-element correction |

## Provider Adaptation

The same structured package can be adapted differently for each provider. For
ComfyUI, ShotForge writes prompt text, API workflow JSON, video artifacts, and
iteration metadata into the run directory.

## Correction Loop

```text
evaluation issue
-> correction plan
-> field-level prompt update
-> provider prompt rewrite
-> regenerated artifact
-> version diff
```

The important rule is that corrections should preserve the run structure. A
missing drone should become a targeted visible-object constraint, not a vague
sentence that only makes the prompt longer.
