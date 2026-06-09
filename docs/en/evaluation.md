# Evaluation

ShotForge evaluates generated video runs as an iterative loop, not as a single
score.

## Layers

Evaluation starts from concrete visual facts and moves toward more subjective
creative qualities:

1. `physical_effect`: required subjects, object count, colors, location,
   weather, and action.
2. `frame_consistency`: whether objects, identities, and actions remain stable
   across frames.
3. `style_color`: style, color palette, lighting, and visual treatment.
4. `emotion_atmosphere`: mood, tension, and atmosphere.
5. `prompt_execution`: whether the generated prompt package follows the user's
   intent and the correction plan.

## Observation

For video runs, ShotForge can extract frames, run a visual observer provider,
and attach observations to the evaluation report. This allows the evaluator to
check what appeared in the rendered artifact rather than only reading the prompt.

## Iteration

When evaluation finds gaps, the correction step can update the prompt/template
package with:

- required visible elements
- missing physical targets
- action constraints
- negative constraints
- version notes

The next generation keeps the previous run available for comparison through
version diffs and run history.
