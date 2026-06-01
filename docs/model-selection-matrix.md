# Model Selection Matrix

ShotForge separates provider selection into LLM/Judge, video generation, and visual observation surfaces. This makes cost, latency, privacy, and quality tradeoffs explicit during a POC.

## Selection Dimensions

| Dimension | What To Compare |
|---|---|
| Quality | Prompt following, visual consistency, factual/physical target match |
| Latency | Time to first result and batch throughput |
| Cost | Token cost, generation cost, wasted retry cost |
| Privacy | Whether prompts, assets, and generated videos leave local environment |
| Reliability | Failure mode, retry behavior, service availability |
| Integration | API stability, workflow support, artifact handling |
| Governance | Logging, policy control, auditability, safety features |

## LLM / Judge Providers

| Provider Type | Best For | Tradeoffs | ShotForge Surface |
|---|---|---|---|
| Mock | Deterministic local tests and demo reliability | No real reasoning quality | `MockLLMProvider` |
| Ollama | Local POC and privacy-sensitive testing | Local hardware limits and slower throughput | `OllamaProvider` |
| vLLM | Local or private high-throughput serving | Requires GPU/server setup | `VLLMProvider` |
| OpenAI-compatible | Enterprise/cloud model integration | Network, cost, credential governance | `OpenAICompatibleProvider` |

## Video Generation Providers

| Provider Type | Best For | Tradeoffs | ShotForge Surface |
|---|---|---|---|
| Mock | Pipeline tests, UI demo, CI stability | No real video quality signal | `MockGenerator` |
| ComfyUI | Local generation, workflow control, private assets | Requires GPU and workflow maintenance | `ComfyUIProvider` |
| Planned cloud providers | Customer benchmark and production deployment | Cost, API differences, credential/security review | Provider adapter boundary |

## Visual Observation Providers

| Provider Type | Best For | Tradeoffs | ShotForge Surface |
|---|---|---|---|
| Prompt proxy | Cheap deterministic evaluation proxy | Cannot verify real pixels | `prompt-proxy` observer |
| OpenAI-compatible vision | Cloud visual inspection and JSON reports | Cost and external data transfer | VLM observer provider |
| Ollama vision | Local privacy-sensitive inspection | Model quality and latency vary | VLM observer provider |
| vLLM VLM | Private high-throughput visual inspection | Requires GPU/server setup | VLM observer provider |

## POC Selection Strategy

```text
Stage 1: Mock providers
  Validate workflow, state, exports, and audit evidence.

Stage 2: Local LLM/Judge
  Validate evaluation and redesign reasoning with controlled cost.

Stage 3: Local or approved video provider
  Validate generation artifacts and observation loop.

Stage 4: Provider benchmark
  Compare quality, latency, cost, retry rate, and operational risk.

Stage 5: Production selection
  Choose provider mix and approval gates based on customer constraints.
```

## Recommendation Template

| Customer Constraint | Recommended Starting Point |
|---|---|
| Needs privacy/local assets | Ollama or vLLM for LLM/Judge, ComfyUI for video |
| Needs fast managed POC | OpenAI-compatible LLM/Judge, mock or available cloud video provider |
| Needs deterministic demo | Mock LLM and mock generator |
| Needs quality benchmark | Run same ProjectState through multiple provider profiles |
| Needs cost control | Evaluate and redesign before final video generation |

## What ShotForge Should Capture

For every provider decision, the run should record:

- provider profile name
- model/provider IDs
- preflight result
- generation artifact paths
- observation provider ID
- evaluation mode
- cost/latency metadata when available
- fallback or failure reason

This makes model selection part of the solution architecture instead of an implicit implementation detail.
