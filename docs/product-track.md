# Product Track

The Product Studio track is the part of ShotForge meant to become a usable AI short-video creation tool.

It should prioritize the full user journey over architectural purity.

## Positioning

ShotForge Product Studio should help a user move from:

```text
idea -> storyboard -> editable plan -> audio/subtitle cues -> preview/export -> refined package/video
```

The product goal is not to expose every internal agent. The product goal is to make the creative workflow feel complete.

## Target User

Primary user:

- Short-video creator.
- Growth/content operator.
- Indie maker testing video ads or social content.
- Technical user who wants controllable AI video planning before paying for expensive generation.

## Product Promise

Input one idea. Get a structured short-video plan that can be reviewed, refined, exported, and eventually rendered into a preview video.

## Current Product Surface

Current Web Demo:

- Idea input.
- Language selection.
- Design / full-loop mode.
- Generator provider selection.
- Storyboard cards.
- Evaluation report.
- Correction plan and version diff view.
- Export links.

Current outputs:

- JSON package.
- CSV storyboard.
- Markdown production package.
- Evaluation CSV.

## Product Roadmap

### P0: Clear Web Demo

Goal: make the existing web demo readable and demo-friendly.

- Improve first-screen layout.
- Show workflow mode clearly.
- Show generated scenes as editable-looking cards.
- Make exports obvious.
- Add empty/error states.
- Add demo screenshots to README.

### P1: Review and Refine

Goal: let the user edit before re-running.

- Inline scene title and description editing.
- Edit prompt package per scene.
- Add review notes.
- Run refine from selected notes.
- Compare before/after package versions.

### P2: Media Planning

Goal: move from abstract production package to production-ready assets.

- TTS provider boundary.
- Subtitle timing plan.
- BGM and sound effect plan.
- Local/media library placeholder.
- Asset manifest export.

### P3: Lightweight MP4 Preview

Goal: generate a real preview artifact without pretending to be a full video model.

- Use still images, text overlays, subtitle cards, and transitions.
- Use ffmpeg or MoviePy to render a preview MP4.
- Export vertical 9:16 and horizontal 16:9.
- Keep quality expectations clear: preview/storyboard video, not final cinematic generation.

### P4: External Video Model Integration

Goal: call real providers only after the plan converges.

- Provider catalog for Kling, Runway, Jimeng, ComfyUI, Open-Sora, or others.
- Cost estimate per run.
- "Cheap iteration, expensive final render" workflow.
- Provider-specific prompt adaptation.

## Product Boundaries

Product Studio should not become a generic video editor.

In scope:

- Creative planning.
- Storyboard editing.
- Prompt refinement.
- Evaluation and correction.
- Preview rendering.
- Export packages.

Out of scope for now:

- Full timeline editing.
- Advanced color/audio mixing.
- Asset marketplace.
- Multi-user collaboration.
- Payment system.

## Success Criteria

The product track is working when a non-engineer can:

1. Open the Web Demo.
2. Enter a video idea.
3. Understand the generated scenes.
4. Make a small edit.
5. Re-run or refine.
6. Download a package or preview artifact.

That is different from the engineering track, where success is judged by code structure, traceability, tests, and extensibility.
