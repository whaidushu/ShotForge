# ShotForge / 镜铸 — 架构设计与模块说明

> 最后更新：2026-05-25 | 版本：V0-V3 完成

---

## 🏗️ 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                      ShotForge 系统                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户入口层                                                      │
│  ┌──────────┬──────────────┬─────────────┐                     │
│  │  CLI     │   Web UI     │   REST API  │                     │
│  │ (Typer)  │  (FastAPI)   │  (FastAPI)  │                     │
│  └────┬─────┴──────┬───────┴──────┬──────┘                     │
│       │            │              │                              │
│  ─ ─ ─ ┼ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─┼ ─ ─ ─ ─ ─ ─                │
│       │            │              │                              │
│  编排层                                                          │
│  ┌──────────────────────────────────────────┐                  │
│  │         LangGraph StateGraph              │                  │
│  │  State → Node → Edge → Checkpoint        │                  │
│  │                                          │                  │
│  │  Workflows:                               │                  │
│  │  ├─ design_workflow.py                    │                  │
│  │  ├─ evaluation_workflow.py                │                  │
│  │  ├─ redesign_workflow.py                  │                  │
│  │  ├─ iterative_redesign_workflow.py        │                  │
│  │  └─ full_loop_workflow.py                 │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                 │
│  协议层                                                          │
│  ┌─────────────────────┬─────────────────────┐                 │
│  │   LLM Provider       │  Generator Provider  │                 │
│  │   (文本生成)          │  (视频生成)          │                 │
│  │   ┌──────────────┐  │  ┌──────────────┐   │                 │
│  │   │ Mock · free   │  │  │ Mock · free   │   │                 │
│  │   │ Ollama · free │  │  │ ComfyUI·local │   │                 │
│  │   │ vLLM · local  │  │  │ Kling · paid  │   │                 │
│  │   └──────────────┘  │  └──────────────┘   │                 │
│  │   LLMRegistry        │  GeneratorRegistry   │                 │
│  └─────────────────────┴─────────────────────┘                 │
│                                                                 │
│  知识 & 评测层                                                    │
│  ┌──────────────────────────────────────────┐                  │
│  │  KnowledgeBase (标签检索)                  │                  │
│  │  EvaluationRubric (9维 + 可配置权重)        │                  │
│  │  CorrectionStrategies (7种策略, zh/en)     │                  │
│  │  EvaluatorProvider (MockVisual+PromptSt)  │                  │
│  │  SignalAggregator (信号→维度分)             │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                 │
│  工程层                                                          │
│  ┌──────────────────────────────────────────┐                  │
│  │  ProjectState (300+字段 Pydantic 状态)    │                  │
│  │  VersionManager (Snapshot/Fork/Diff)     │                  │
│  │  ConvergenceEngine (6种停止条件)          │                  │
│  │  RegressionCheck (ScoreDelta+回归检测)    │                  │
│  │  TraceLog (执行追踪)                      │                  │
│  └──────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 模块详解

### 1. LLM Provider 模块 (`src/shotforge/llm/`)

**职责：** 为所有 Agent 提供文本生成能力。Agent 不直接调 LLM API，而是通过 `LLMProvider` 协议调用。

| 文件 | 说明 |
|------|------|
| `provider.py` | `LLMProvider` Protocol — 定义 `complete()` / `acomplete()` / `stream()` 接口 |
| `mock.py` | `MockLLMProvider` — 确定性 Mock，SHA1 输出，开发测试用 |
| `ollama.py` | `OllamaProvider` — 本地 Ollama 模型，OpenAI 兼容 API，cost=free |
| `vllm.py` | `VLLMProvider` — 本地 vLLM GPU 推理，OpenAI 兼容 API，cost=local |
| `registry.py` | `LLMRegistry` — 注册/获取/列表/可用性检查 + `build_llm_catalog()` |

**设计原则：** Protocol 而非 ABC——任何有 `complete()` 方法的类都是 LLMProvider，不需要显式继承。

**调用链：**
```
AgentHarness.build_default_registry()
  → SkillRegistry.register("llm.complete", MockLLMProvider().complete)

intent_agent()
  → registry.call("llm.complete", prompt, purpose="intent")
  → MockLLMProvider.complete() → 确定性输出
```

---

### 2. Generator Provider 模块 (`src/shotforge/generators/`)

**职责：** 将 `ProjectState` 中的设计包转换为实际视频/图片。

| 文件 | 说明 |
|------|------|
| `base.py` | `GeneratorProvider` Protocol + `GenerationCostEstimate` + `GeneratorCapabilities` |
| `mock_generator.py` | `MockGenerator` — 确定性 Mock，可用于开发测试 |
| `comfyui_provider.py` | `ComfyUIProvider` — 对接本地 ComfyUI API，支持任意模型 |
| `registry.py` | `GeneratorRegistry` + Catalog（mock/comfyui 可用，其余 planned） |

**成本模式：** `free`(Mock) / `local`(ComfyUI) / `paid`(Kling/Runway)

**ComfyUIProvider 工作原理：**
```
1. 从 ProjectState 提取每个 shot 的 prompt
2. 根据 provider profile 选择内置或用户本地 API-format workflow
3. 注入 prompt、seed、尺寸、帧数、FPS 等运行参数
4. 调用 ComfyUI /prompt 提交 workflow
5. 轮询 /history/{prompt_id} 等待完成
6. 解析 ComfyUI 输出并下载 MP4 / 图片 / workflow 产物
7. 按 iteration 写入 data/runs/{run_id}/iterations/v*/
8. 构造 GeneratedShotResult → GeneratedResult
```

**当前能力：** 支持内置 `wan2_2_i2v_empty_start` 视频工作流，也支持查询用户本地 ComfyUI workflow 目录并调用 API-format workflow。本地测试 provider 仅用于无模型环境下验证流程，不作为默认生成路径。

---

### 3. Agent 体系 (`src/shotforge/agents/`)

#### 3.1 设计 Agent (`agents/design/`) — 5 个

| Agent | 职责 | 是否需要 LLM |
|-------|------|:---:|
| `intent_agent.py` | 解析创意，推断 genre/mood/约束 | ✅ 唯一调 LLM 的 |
| `storyboard_agent.py` | 生成 Scene/Shot 规格 | ❌ 规则驱动 |
| `motion_agent.py` | 分配镜头运动和转场 | ❌ 规则驱动 |
| `audio_cue_agent.py` | 分配音乐和音效 | ❌ 规则驱动 |
| `prompt_adapter_agent.py` | 生成每个 shot 的视频生成 Prompt | ❌ 模板驱动 |

**设计模式：** 纯函数 `agent(state) -> state`，通过 LangGraph Node 串联。

#### 3.2 评估 Agent (`agents/evaluation/`) — 4 个

| Agent | 职责 |
|-------|------|
| `verification_agent.py` | 检查生成结果的结构完整性 |
| `evaluation_agent.py` | 按 Rubric 对 GeneratedResult 打分 |
| `suggestion_agent.py` | 根据 Issues 生成 CorrectionPlan |
| `correction_router.py` | 将 Plan 路由到对应的 CorrectionAgent |

#### 3.3 修正 Agent (`agents/correction/`) — 7 个

| Agent | 修正类型 | 修正什么 |
|-------|---------|---------|
| `action_correction_agent.py` | action | 动作清晰度和节奏 |
| `emotion_correction_agent.py` | emotion | 情绪强度和表达 |
| `prompt_correction_agent.py` | prompt | 提示词可执行性 |
| `character_correction_agent.py` | character | 角色一致性 |
| `scene_correction_agent.py` | scene | 场景一致性 |
| `camera_correction_agent.py` | camera | 镜头表达 |
| `audio_correction_agent.py` | audio | 音频时序 |

**修正策略：** 每种修正类型在 `knowledge/correction_strategies.json` 中有对应的 zh/en 文案模板。Agent 只生成结构化 `CorrectionPatch`，不直接改状态。

---

### 4. Workflow 模块 (`src/shotforge/workflows/`)

| Workflow | 流程 | 用途 |
|----------|------|------|
| `design_workflow.py` | Idea → 5 Agent → ProjectState | 仅生成方案包 |
| `evaluation_workflow.py` | ProjectState → Mock/Real Generate → Eval | 生成+评估 |
| `full_loop_workflow.py` | Design + Evaluation | 一键设计+评估 |
| `redesign_workflow.py` | IssueList → Correction → ReGenerate → ReEval | 单轮修正 |
| `iterative_redesign_workflow.py` | 多轮 Redesign + ConvergenceEngine | 迭代收敛 |

**完整环路：**
```
Design → Generate → Evaluate → Redesign → ReGenerate → ReEvaluate
   ↑                                                          ↓
   └──────────── ConvergenceEngine 判断继续/停止 ──────────────┘
```

---

### 5. 核心模块 (`src/shotforge/core/`)

| 文件 | 职责 |
|------|------|
| `project_state.py` | 300+ 字段 Pydantic 状态模型，贯穿全流程 |
| `context_builder.py` | 为 Agent 构建上下文（注入知识库） |
| `knowledge_base.py` | 基于标签检索的知识库 |
| `rubrics.py` | 加载评估量表配置 |
| `trace_log.py` | 执行事件追踪和耗时记录 |
| `version_manager.py` | 版本快照、fork、diff |
| `convergence_engine.py` | 6种停止条件判断 |
| `regression_check.py` | ScoreDelta 计算和回归检测 |
| `schemas/` | 评估 Rubric 子模型 |

---

### 6. 收敛引擎 (`ConvergenceEngine`)

**6 种停止条件：**

| 条件 | 说明 |
|------|------|
| `max_iterations_reached` | 达到用户配置的上限 (2-10轮，默认3) |
| `design_package_unchanged` | 生产包无有效变化，提前截断 |
| `regression_detected` | 检测到评分回归 |
| `score_delta_below_threshold` | 评分提升低于阈值 (默认0.005) |
| `all_tracked_issues_resolved` | 所有追踪问题已解决 |
| `continue` | 以上均不满足，继续迭代 |

**收敛步骤记录：** 每轮迭代记录 `ConvergenceStep`，包含 `ScoreDelta`、`RegressionCheck`、`StopCondition`。

---

### 7. 版本管理 (`VersionManager`)

```
V1 (设计包) → Generated V1 → Eval Report V1
                                  ↓ Issues
                            Correction Plans
                                  ↓ Patches
V2 (修正版) → Generated V2 → Eval Report V2
                                  ↓
                        VersionDiff (V1 vs V2):
                          - changed_shots
                          - changed_prompts
                          - changed_audio_cues
                          - resolved_issues
                          - new_issues
```

**核心能力：**
- `save_snapshot()` — 持久化版本快照
- `fork_next_version()` — 从旧版本 fork 出新版本
- `VersionDiffBuilder` — 追踪字段级变化、prompt 变化、问题解决情况
- `/api/runs/{run_id}/versions` — Web 查看版本历史
- Web Version Chain — 展示 version diff、prompt changes、run history 和 per-iteration artifacts

---

### 8. 评估体系

**9 维评估维度（配置驱动，JSON 可调）：**

| 维度 | 权重 | 修正类型 |
|------|:---:|---------|
| `character_consistency` | 1.0 | character |
| `scene_consistency` | 1.0 | scene |
| `action_clarity` | 1.2 | action |
| `emotional_intensity` | 1.1 | emotion |
| `camera_expression` | 1.0 | camera |
| `pacing_progression` | 1.0 | action |
| `reversal_expression` | 0.8 | emotion |
| `audio_timing` | 0.9 | audio |
| `prompt_executability` | 1.1 | prompt |

**信号流：**
```
EvaluatorProvider.evaluate()
  → [EvaluationSignal]  (每个 shot 每个维度一个信号)
  → SignalAggregator    (按维度聚合)
  → DimensionScore      (0-1 分)
  → Issue               (< 阈值的维度)
  → CorrectionPlan      (按修正类型分组)
```

---

### 9. 入口层

| 入口 | 文件 | 参数示例 |
|------|------|---------|
| **CLI** | `app/cli/main.py` | `shotforge full-loop "创意" --generator comfyui --llm ollama` |
| **Web** | `app/web/app.py` | 页面表单，下拉选择 Provider |
| **API** | `app/web/app.py` | `POST /api/runs` JSON body |

**三种入口共享同一套 Workflow 和 Provider 体系。**

---

### 10. 导出器 (`src/shotforge/exporters/`)

| 导出器 | 输出文件 | 说明 |
|--------|---------|------|
| `json_exporter.py` | `package.json` | 完整 ProjectState |
| `csv_exporter.py` | `package.csv` | 分镜表（utf-8-sig） |
| `markdown_exporter.py` | `package.md` | 可读的 Markdown 文档 |
| `evaluation_csv_exporter.py` | `evaluation.csv` | 评估报告 |
| `mp4_exporter.py` | `{run_id}.mp4` | FFmpeg 拼接成片 |

---

## 🔌 Protocol 模式说明

ShotForge 大量使用 Python `Protocol`（结构子类型/鸭子类型）而非传统的 `ABC`（继承）。

### 为什么不用 ABC

```
ABC 要求：class MyProvider(ABCBase)    ← 必须显式继承
Protocol：class MyProvider: ...        ← 有正确方法签名就行
```

**关键区别：**
- `ABC` 在运行时检查继承链——不继承就报错
- `Protocol` 在运行时检查方法签名——有就行，不关心继承
- `Protocol` 配合 `@runtime_checkable` 允许 `isinstance(obj, Protocol)`

**ShotForge 中的应用：**
- `LLMProvider`: 任何有 `complete()` 方法的类都符合
- `GeneratorProvider`: 任何有 `generate()` 方法的类都符合
- 第三方 SDK 类不需要继承我们的类，只要方法对就行

---

## 🧩 关键设计决策

| 决策 | 原因 |
|------|------|
| Protocol 而非 ABC | 不侵入继承链，第三方库也可以适配 |
| SkillRegistry 而非硬编码 | 允许运行时替换 LLM/Generator |
| Pydantic v2 全量状态模型 | 类型安全 + 自动序列化 + JSON 持久化 |
| 配置驱动评估量表 | 9维权重/阈值/修正类型全部 JSON 可配 |
| 版本迭代 + 快照 | 每次修正可追溯，支持回归检测 |
| 先 Mock 再真实 | Mock 保证环路逻辑正确，再接入昂贵 API |
| 小模型迭代 + 大模型交付 | 本地免费迭代 50 轮，商业 API 只最后一次 |
