# AI Video Workbench Layer

The AI Video Workbench layer is the user-facing surface of ShotForge. It turns
the Agent Harness runtime into a short-video production workspace where a user
can configure providers, run a generation loop, inspect prompt changes and
artifacts, review evaluation results, compare versions, and export a handoff
package.

## Current Product Surface

The current Web app is organized around two pages:

- **Workflow page**: idea input, mode selection, run progress, storyboard,
  prompt changes, generated videos, evaluation reports, correction plans,
  version chain, and exports.
- **Configuration page**: provider profiles, LLM/Judge settings, video provider
  settings, ComfyUI workflow discovery, visual observer settings, preflight, and
  local readiness testing.

The workbench is intentionally profile-driven. Normal users should select or
save a provider profile instead of passing local service URLs in every run
request.

## Product Completeness Layer

The current product work is not a full UI redesign. It is a reviewer-facing
completion layer that makes the existing runtime readable as a tool:

- **Curated sample first**: a public reviewer can open `/demo?language=en` and
  inspect a completed run without configuring GPU services.
- **Run as the product object**: the workbench frames each video job as a run
  with lifecycle, provider profile, artifacts, evaluation, versions, exports,
  and audit evidence.
- **Configuration is separate**: provider readiness lives on the Configuration
  page so the creative workflow is not mixed with local service details.
- **Handoff is visible**: exports, readiness gates, trace, and package files are
  presented as delivery artifacts, not hidden implementation files.

This is the minimum product layer needed before deeper UI polish. It lets a
reviewer understand the workflow in minutes while still making the Agent
Harness evidence available underneath the workbench.

## Current User Flow

```text
Configure provider profile
-> Run preflight
-> Enter idea
-> Generate design package
-> Render video artifact when a video provider is configured
-> Extract frames and observe visual facts
-> Evaluate physical / consistency / style / atmosphere layers
-> Create correction plan
-> Regenerate or export
-> Compare versions and handoff artifacts
```

## What The Workbench Should Make Visible

- Which provider profile is active.
- Whether LLM, video, workflow, and observer services are ready.
- What prompt changed between iterations.
- Which video artifact belongs to each iteration.
- Which physical targets were required, observed, and missing.
- Which evaluation issues drove the correction plan.
- Which files can be exported or handed off.

## Current Boundaries

In scope now:

- Single-shot workflow with a path toward multi-shot expansion.
- Provider profile configuration and local readiness checks.
- ComfyUI workflow discovery and API-format workflow execution.
- Prompt, workflow, video, frame, evaluation, and export artifacts.
- Version history and prompt/evaluation diffs.
- Layered evaluation from physical facts toward more abstract quality signals.

Out of scope for the current workbench:

- Full timeline editing.
- Multi-user collaboration.
- Payment, quota, and account management.
- Production deployment packaging.
- Asset marketplace or full media library.

## Next Product Direction

The next product work should stay close to the current framework:

- Improve the run workbench layout and artifact comparison.
- Make physical target extraction and missing-element correction easier to see.
- Add stronger multi-shot data structures without forcing multi-shot UI early.
- Keep configuration separate from the creative workflow.
- Reduce deployment friction without hiding provider readiness requirements.
