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
