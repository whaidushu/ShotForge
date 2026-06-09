# Providers

ShotForge separates provider types so a run can use different services for text
reasoning, video rendering, and visual inspection.

## Provider Types

- **LLM/Judge**: prompt generation, prompt revision, and LLM-as-judge scoring.
- **Video**: MP4 generation through a local or external renderer.
- **Visual Observer**: frame and sequence inspection for generated videos.

## Supported Paths

| Type | Provider examples | Typical use |
| --- | --- | --- |
| LLM/Judge | Ollama, vLLM, OpenAI-compatible APIs | local or API-based text reasoning |
| Video | ComfyUI, test provider | real local rendering or deterministic tests |
| Visual Observer | prompt-proxy, OpenAI-compatible vision, Ollama vision, vLLM VLM | observe rendered frames |

The test provider is useful for development and CI. For real generation, use a
configured LLM/Judge provider and a video provider such as ComfyUI.

## ComfyUI

ComfyUI integration requires:

- a running ComfyUI server
- an API-format workflow
- a workflow ID selected in the provider profile
- output paths that ShotForge can resolve after execution

Use the Web configuration page to search workflows, select one, and run
preflight before creating a full run.

## Visual Observation

Visual observer providers inspect extracted frames and produce observations that
evaluators can compare with the requested prompt. This is the path used for
checks such as required objects, location, weather, action, and frame-to-frame
consistency.
