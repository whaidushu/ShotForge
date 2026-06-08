# UI Engineering Framework

ShotForge's Web UI should be treated as a product surface, not a demo template. The current foundation keeps the UI easy to redesign while preserving the run and provider workflow.

## Directory Model

```text
src/shotforge/
  templates/
    index.html                 Server-rendered product shell
  app/web/static/
    design-system.css          Tokens, layout primitives, reusable component classes
    shotforge-ui.js            Provider forms, preflight, workflow search, tabs, and run shell behavior
    README.md                  Static asset ownership notes
```

Future assets should be added under `app/web/static`:

```text
app/web/static/
  icons/                       Curated SVG icon set or generated sprite
  images/                      Product images, empty-state media, thumbnails
  motion/                      Lottie or JSON animation assets
  components/                  CSS modules for reusable UI components
```

## Design System Rules

- Use `design-system.css` for tokens, layout primitives, icon buttons, motion utilities, and shared component styling.
- Keep feature-specific layout in the template only until it is reused by more than one view.
- Keep executable browser behavior in `shotforge-ui.js`; templates should expose data through a small bootstrap object, not large inline scripts.
- Prefer semantic component classes such as `.sf-toolbar`, `.sf-sidebar-layout`, and `.sf-icon-button`.
- Keep animation opt-in and respect `prefers-reduced-motion`.
- Keep icons, motion, and generated images as managed assets instead of inline one-off markup.

## Product Pages

The Web product should stay split into clear user workflows:

- Workflow page: idea, mode, generation controls, progress, prompt changes, videos, and exports.
- Configuration page: provider profiles, LLM/Judge settings, video provider
  settings, ComfyUI workflow discovery, preflight, and local readiness checks.
- Visual observer configuration: VLM provider, model, base URL, API key, frame sample count, confidence threshold, and JSON requirement.
- Run detail sections: progress timeline, prompt diff cards, generated artifact browser, evaluation, correction plans, readiness, and exports.

## Engineering Boundary

UI code should call Web/API routes only. Provider configuration, run creation, artifact lookup, and history are owned by:

- `ProviderService`
- `RunService`
- `ArtifactService`

This keeps future UI polish work focused on presentation while the generation workflow remains testable from API and CLI entrypoints.

## Current Layout Direction

The Web UI is moving toward a studio workbench rather than a single long form:

- Left rail: task creation and run history.
- Center surface: current run status, videos, prompt changes, evaluation, and version progress.
- Right rail: provider and service configuration.
- Configuration page: deeper provider profile editing, local workflow search,
  preflight, and readiness testing.

Future UI iterations should preserve this split so provider complexity does not crowd the creative workflow.

## Current Interaction Modules

`shotforge-ui.js` currently owns:

- profile selection and form synchronization
- LLM/video/observer config visibility
- provider profile save
- provider preflight
- local readiness test trigger
- ComfyUI local workflow search
- run form submission state
- run detail tabs

Provider fields are only synchronized when the user changes the selected
profile. Submitting a run preserves any manual field edits, which is important
when a user is testing a new ComfyUI URL, workflow directory, or VLM model before
saving it as a reusable profile.
