# ShotForge 分层评测与收束设计

当前实现把“可插拔评测维度”升级为“可插拔、可分层的评测体系”。核心目的不是把维度一次性定死，而是让后续新增维度、调整优先级、改变收束策略时，只改配置和局部 evaluator。

## 当前层级

层级定义在 `src/shotforge/knowledge/evaluation_rubrics.json`。

| 层级 | layer_id | 当前职责 |
| --- | --- | --- |
| L1 | `hard_targets` | 主体、角色、场景等直接可观测硬约束 |
| L2 | `motion_timing` | 动作清晰度、节奏推进 |
| L3 | `cinematic_expression` | 镜头语言是否服务叙事 |
| L4 | `narrative_emotion` | 情绪、反转、声音点位 |
| L5 | `prompt_execution` | Prompt 字段是否足够可执行 |

规则：`layer_index` 越小，越先修。`SuggestionAgent` 会先找当前报告里最低层的问题，只为这一层生成 `CorrectionPlan`，更高层问题进入 `RedesignPlan.defer_issue_ids`，避免一轮里同时修底层事实和高层风格导致目标发散。

## 关键状态

- `StructuredPromptTemplate`：挂在每个 `PromptItem.structured_template` 上，用字段承载可回写内容。
- `EvaluationDimensionConfig.layer_id/layer_index`：每个评测维度归属一个层。
- `EvaluationDimensionConfig.prompt_fields`：标明该维度主要影响哪些结构化 prompt 字段。
- `EvaluationReport.score_card.metadata.layers`：每次评测输出层级摘要。
- `Issue.metadata.layer_id/layer_index/prompt_fields`：问题保留层级和回写字段定位。
- `RedesignPlan`：记录本轮要修哪一层、修哪些 issue、保护哪些字段、延后哪些 issue。
- `CorrectionPlan.metadata.layer_id/layer_index/prompt_fields`：修正计划继承层级和字段定位。

## 新增评测维度

在 `evaluation_rubrics.json` 的 `dimensions` 里新增一项即可：

```json
{
  "id": "subject_count",
  "labels": {"zh": "主体数量", "en": "Subject Count"},
  "weight": 1.0,
  "target": "The generated result contains the requested number of primary subjects.",
  "signal_key": "subject_count",
  "layer_id": "hard_targets",
  "layer_index": 1,
  "prompt_fields": ["character_identity"],
  "hard_target": true,
  "issue_rule": {
    "threshold": 0.9,
    "correction_type": "character",
    "description_templates": {
      "zh": "{shot_id} 的主体数量不符合目标。",
      "en": "Subject count in {shot_id} does not match the target."
    },
    "cause_templates": {
      "zh": "主体数量约束不够明确。",
      "en": "Subject count constraint is not explicit enough."
    },
    "description_template": "Subject count in {shot_id} does not match the target.",
    "cause_template": "Subject count constraint is not explicit enough."
  }
}
```

如果是已有 evaluator 能产生的信号，只要 `signal_key` 和 `dimension_id` 对齐即可。若需要新的信号来源，再新增一个 `EvaluatorProvider` 并注册到 `EvaluatorRegistry`。

## 新增 Prompt 字段

先在 `StructuredPromptTemplate` 增加字段，再在 `prompt_adapter_agent.py` 初始化该字段，最后让 rubric 里的维度通过 `prompt_fields` 指向它。这样 Evaluation → Issue → RedesignPlan → CorrectionPlan 都能携带字段定位。

后续可以把 `CorrectionOperation` 从当前的 append 型操作升级为字段级替换、合并和保护策略，接口已经通过 `field_path` 和 `prompt_fields` 预留了方向。
## Physical Effect Layer

The first convergence layer is now `physical_effect`. It is intentionally strict and checks directly observable facts before style or narrative optimization:

- `subject_count`: requested primary subject count is preserved.
- `color_alignment`: named colors and visible color attributes are preserved.
- `element_presence`: required props, scene anchors, and visual elements are present.
- `element_description`: physical attributes are concrete enough to generate and evaluate.

The evaluator is `physical_effect_static`. It reads `GeneratedShotResult.detected_elements` and `observed_summary` when a provider or future CV/VLM observer supplies them. If no visual observation is available, it falls back to the structured prompt as a proxy and records `visual_observation_missing=true` in signal metadata. This keeps the framework usable today while leaving a clean replacement point for real frame/video inspection.
# Current Layer Model

ShotForge now uses a from-real-to-abstract convergence order:

| Layer | layer_id | Responsibility |
| --- | --- | --- |
| L0 | `physical_effect` | Single-shot physical facts: subject count, object existence, required elements, concrete element descriptions. |
| L1 | `frame_consistency` | Single-shot frame-to-frame stability now; multi-shot continuity later. Covers element drift, action drift, and face/identity drift. |
| L2 | `style_color` | Color alignment, visual style, and camera language after facts and consistency are stable. |
| L3 | `emotion_atmosphere` | Emotion, atmosphere, reveal/reversal, audio timing, and other soft expressive goals. |
| L4 | `prompt_execution` | Prompt completeness and executability, checked throughout as a technical support layer. |

The current product flow starts with one generated shot. Future multi-shot support should reuse the same layer ids and add shot-level observations beside frame-level observations instead of changing `EvaluationReport`.

`FrameConsistencyEvaluator` reads future-ready `GeneratedShotResult.metadata.frame_observations`:

```json
[
  {
    "frame_index": 0,
    "detected_elements": ["woman", "red umbrella"],
    "face_identity": "woman_a",
    "action_summary": "woman lifting umbrella"
  }
]
```

If frame observations are missing, the evaluator emits a single-shot baseline signal with `single_shot_mode=true` and `frame_observation_missing=true`; this keeps today's single-shot flow stable while reserving the interface for real frame/VLM inspection.

## Observation Pipeline

Generated videos are observed before verification and evaluation:

```text
Generate video -> extract frames -> observe frames -> write frame_observations -> evaluate consistency
```

The implementation lives in `shotforge.observation`:

- `VideoFrameExtractor`: uses local `ffmpeg` when available to extract sampled frames from a generated MP4.
- `HeuristicFrameObserver`: fills frame observations from prompt/package context when no VLM is connected yet.
- `VLMFrameObserver`: adapts external frame descriptions into `FrameObservation`.
- `observation.providers`: selects prompt-proxy, OpenAI-compatible vision, Ollama vision, or vLLM VLM providers from runtime configuration.
- `VideoObservationService`: updates each `GeneratedShotResult.metadata.frame_observations` before evaluators run.

This is intentionally single-shot first. Multi-shot support should add shot-level or sequence-level observations alongside the existing per-shot `frame_observations`.

## Physical Target Contract

The physical layer now extracts hard targets from the user idea before prompt generation. A request such as `A cyber cat chases a glowing drone across rainy Shanghai rooftops` becomes a target contract containing:

- required elements: cyber cat, glowing drone, Shanghai, rooftop, rainy night
- action: chasing
- subject count: one primary subject

These targets are injected into creative intent, storyboard key visuals, structured prompt fields, success criteria, and negative prompts. During evaluation, missing observed elements become low-layer issues so the redesign loop corrects physical facts before abstract style or mood.

`prompt-proxy` keeps the loop runnable when no visual model is configured, but real improvement should use an observer provider that inspects frames from the rendered video.
