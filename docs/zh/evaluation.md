# 评估

ShotForge 把评估作为迭代 workflow，而不是单次打分。系统会检查生成 artifact 是否匹配用户创意，
识别缺口，写入 correction plan，并保留版本证据用于对比。

## 评估流水线

```text
ProjectState
-> generated video artifact
-> frame extraction
-> visual observation
-> evaluator registry
-> score card and issues
-> correction plan
-> prompt/template patch
-> regenerated version
-> score delta and regression check
```

## 分层

评估从具体视觉事实开始，再逐步走向更抽象的创意质量：

| Layer | 检查内容 | 示例信号 |
| --- | --- | --- |
| `physical_effect` | 必须可见的事实 | 主体数量、物体、颜色、地点、天气、动作 |
| `frame_consistency` | 帧间稳定性 | 元素连续性、动作连续性、身份稳定性 |
| `style_color` | 视觉处理 | 色彩、光照、风格匹配 |
| `emotion_atmosphere` | 表达质量 | 情绪、张力、氛围 |
| `prompt_execution` | prompt/package 质量 | prompt 覆盖、约束、correction 执行 |

## 物理目标

`src/shotforge/core/physical_targets.py` 会从用户 idea 中抽取具体目标，包括：

- primary subject
- required objects
- location and setting
- weather or atmosphere
- action
- explicit counts

这些目标会转换为 prompt constraint 和 evaluation expectation。例如用户要求发光无人机，
physical-effect evaluator 可以标记生成 artifact 中没有无人机类元素的问题。

## 物理收敛

`src/shotforge/core/physical_convergence.py` 会把 physical-effect 评估转换成目标级迭代证据：

- 必须可见元素的 target score
- 缺失或较弱元素的 repair target
- 已经可见元素的 preservation lock
- 接受或拒绝重新生成版本的 candidate gate
- 候选版本仍然缺失或回归时的 next revision focus

内置 effect demo 使用这个模块生成 v1/v2/v3 对比；主 redesign workflow 也在普通
full-loop evaluation 之后使用同一个模块。这意味着 demo case 和平台能力是分离的：
示例特定的标签、目标和 prompt patch 保留在 `examples/effect_cases`，候选接受、
回归检查和收敛记录保留在核心 workflow 层。

## 视觉观察

`VideoObservationService` 在生成后运行：

1. 从 shot metadata 定位生成视频文件
2. 抽取采样帧
3. 调用配置的 frame observer
4. 构建 shot observations
5. 构建 sequence observations
6. 将 observation reports 附加到 `ProjectState`

Observation record 包含 frame path、detected elements、action summary、identity summary、
confidence 和 metadata。

## Evaluator Registry

`EvaluatorRegistry.defaults()` 会根据 settings 注册 evaluator：

- `PhysicalEffectEvaluator`
- `FrameConsistencyEvaluator`
- `MockVisualEvaluator`，当 mode 为 `mock` 或 `hybrid`
- `PromptStaticEvaluator`，当 mode 为 `mock` 或 `hybrid`
- `LLMStoryPromptEvaluator`，当 mode 为 `llm` 或 `hybrid`

## 分数与问题

`EvaluationReport` 包含：

- `score_card.overall_score`
- dimension scores
- issues
- strengths
- suggested focus
- rubric id
- metadata

每个 issue 包含：

- severity：`low`、`medium`、`high` 或 `critical`
- dimension id 和 label
- 可选 shot id
- description
- evidence
- suspected cause
- correction type

## 修正与版本

发现问题后，correction planning 可以创建：

- `CorrectionPlan`
- `RedesignPlan`
- `CorrectionPatch`
- `CorrectionOperation`

支持的 patch operation 会追加或更新目标字段，例如 shot description、motion、prompt text、
negative prompt、structured template fields、scene description、audio sound design、
character behavior。

重新生成后，ShotForge 会构建：

- `VersionDiff`
- `ScoreDelta`
- `RegressionCheck`
- `ConvergenceStep`

这些记录解释变更内容、分数是否提升、哪些问题已解决、是否出现新问题。

对于 physical-effect redesign，`RegressionCheck.metadata` 和
`ConvergenceStep.metadata` 还会包含 `physical_convergence_candidate_gate`。如果候选版本
回归了已经锁定的物理目标，或者目标级分数下降超过容忍范围，候选会被标记为 rejected，
metadata 中的 accepted version 会保持为源版本。

## Rubric

Rubric 通过 `RubricStore` 加载，使用以下类型化配置：

- `EvaluationLayerConfig`
- `EvaluationDimensionConfig`
- `EvaluationIssueRule`
- `EvaluationRubric`

Dimension 会定义目标描述、权重、layer mapping、signal key、hard-target flag 和 issue threshold。

## 实际用途

评估用于回答：

- 必须出现的物体是否真的出现？
- 场景和动作是否符合 idea？
- 物体或身份是否在帧间变化？
- 第二次生成是否比第一次更好？
- 版本之间 prompt constraint 改了什么？
- 导出前还有哪些问题？
