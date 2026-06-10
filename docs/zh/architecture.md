# 架构

ShotForge 围绕一个核心对象组织：带版本的视频生成 run。一次 run 从用户创意开始，
经过 provider-backed 生成和评估，最终形成包含 artifact 和 export 的本地 package。

## 分层概览

```text
Web / CLI / API
  -> App services
  -> LangGraph workflows
  -> Workflow Runtime
  -> Provider adapters
  -> ProjectState + artifacts
```

ShotForge 把用户工作台和执行运行时分开：

- **AI 视频工作台**：页面、API、run history、provider 配置、artifact 访问、进度、
  生命周期状态和导出。
- **Workflow Runtime**：类型化状态、上下文构建、agent contract、tool record、
  provider 边界、trace log、版本快照和 policy record。

## Run 流程

```text
idea
-> provider profile
-> ProjectState
-> design package
-> prompt/template package
-> video provider artifact
-> frame extraction
-> visual observation
-> layered evaluation
-> correction plan
-> regenerated package/artifact
-> version diff
-> exports
```

Design-only run 在 prompt package 和导出后停止。Full-loop run 会继续生成、观察、
评估、readiness 和导出。Planning run 会追加迭代 redesign 和版本对比。

## 入口层

### Web

`src/shotforge/app/web/app.py`

Web 层渲染工作台和配置页。它和 API 使用同一组 service，保证 UI 和自动化行为一致。

重要路由：

- `/`：workflow 页面
- `/config`：provider 配置页
- `/demo`：内置 sample run
- `/runs`：Web 表单创建 run 的 POST 入口

### API

`src/shotforge/app/api/`

Router 按用途拆分：

- `system.py`：health 和 capability catalog。
- `runs.py`：run 创建、package 加载、artifact、status、versions、exports。
- `providers.py`：profiles、preflight、workflow discovery、observer providers。
- `schemas.py`：API 请求和响应模型。

### CLI

`src/shotforge/app/cli/main.py`

CLI 命令调用同一套 workflow 和 service：

- `design`
- `full-loop`
- `evaluate`
- `inspect`
- `audit`
- `capabilities`
- `comfyui-workflows`
- `doctor`
- `web`

## 应用服务层

`src/shotforge/app/services/`

| Service | 职责 |
| --- | --- |
| `RunService` | 创建 run、应用 provider profile、选择 run mode、写导出、记录 job 状态。 |
| `ProviderService` | 列出 provider、从 payload/form 构建 profile、校验 generator id、应用 scoped runtime settings。 |
| `ProviderProfileStore` | 读写 `data/provider_profiles.json`，公开响应中脱敏 secret。 |
| `ProviderPreflightService` | 检查 LLM/Judge、视频 provider、workflow 和视觉观察 readiness。 |
| `ComfyUIWorkflowService` | 发现内置和本地 API-format workflow，并报告 callability。 |
| `ArtifactService` | 把 run metadata 映射为 video、prompt、prompt JSON 和 workflow artifact 路径。 |
| `RunStatusService` | 构建 dashboard summary、lifecycle stage、readiness score、timeline 和 handoff 数据。 |
| `RunJobService` | 记录 run progress、failed/completed job 状态。 |

这些 service 把 Web/API 行为和 workflow 实现细节隔离开。

## 核心状态模型

`src/shotforge/core/project_state.py`

`ProjectState` 是 workflow、agent、provider、evaluator、exporter 和 Web/API 共享的类型化状态。
它包含：

- identity：`project_id`、`run_id`、`version`
- 用户输入：`user_idea`、`style`、`duration_seconds`、`target_platform`
- 设计：`creative_intent`、`characters`、`scenes`、`shots`、`audio_cues`
- 提示词：`prompt_package`、`PromptItem`、`StructuredPromptTemplate`
- 生成：`generation_results`、`GeneratedResult`、`GeneratedShotResult`
- 观察：`observation_reports`、frame observations、sequence observations
- 评估：`evaluation_reports`、`issue_history`、`verification_reports`
- 迭代：`redesign_plans`、`correction_plans`、`correction_patches`、
  `version_diffs`、`score_deltas`、`regression_checks`、`convergence_steps`
- 交付：`delivery_readiness`、`exports`
- 运行时证据：trace logs、tool calls、state transitions、context snapshots、
  workflow decisions、memory records、sandbox records、access records

## Package View

`src/shotforge/core/packages.py`

完整 state 适合持久化，但 UI 通常需要分组结构。`ProjectPackageView` 会把 state 拆成：

- `design`
- `generation`
- `observation`
- `evaluation`
- `iteration`
- `runtime`

API 通过 `GET /api/runs/{run_id}/package-view` 暴露该结构。

## Workflow 层

`src/shotforge/workflows/`

Workflow 负责 agent 和 provider 调用顺序：

- design workflow：创建 creative intent、scenes、shots、prompts、exports。
- full-loop workflow：追加 generation、observation、evaluation、readiness。
- iterative redesign workflow：应用 correction plan、重新生成、比较版本。
- evaluation workflow：评估已有 package。

物理收敛属于核心 workflow 能力，而不是只服务于示例 demo。
`src/shotforge/core/physical_convergence.py` 提供目标级摘要、修复计划、preservation lock
和 candidate gate。effect demo 会调用这个模块完成一个固定 case 的 v1/v2/v3 对比；
`redesign_workflow` 也会在主 run 生命周期里针对普通 physical-effect 问题使用同一套能力。

## 运行时证据

`src/shotforge/core/harness_runtime.py`

运行时会在 agent 执行期间记录：

- context snapshots
- contract reports
- workflow decisions
- state transitions
- tool calls 和 orchestration records
- memory selections
- sandbox policy records
- access records

这些信息通过 `shotforge audit` 和 `GET /api/runs/{run_id}/runtime-evidence` 暴露。

## Provider 边界

ShotForge 将 provider 拆成三类：

- LLM/Judge provider 负责文本决策和修订。
- Video provider 负责渲染 artifact。
- Visual observer provider 负责检查帧。

Provider 设置保存在 provider profile 中，并在 run 执行期间通过 scoped runtime context 应用。
这样核心状态逻辑不需要直接耦合具体 provider 配置。

## Artifact 布局

默认 run 数据写入：

```text
data/runs/{run_id}
```

常见文件：

- `package.json`
- `package_view.json`
- `package.csv`
- `package.md`
- `manifest.json`
- `trace.json`
- `run_summary.md`
- `evaluation.csv`
- generated videos
- per-shot prompt text
- per-shot prompt JSON
- provider workflow payloads
- extracted frames

版本快照存放在 `data/versions`。

## 扩展点

主要扩展点：

- 在 `src/shotforge/generators/` 添加 generator provider
- 在 LLM provider registry 中添加 LLM/Judge provider
- 在 `src/shotforge/observation/providers/` 添加 visual observer provider
- 在 `src/shotforge/evaluators/` 添加 evaluator
- 在 `src/shotforge/exporters/` 添加 exporter
- 在 `src/shotforge/workflows/` 添加 workflow node
- 在 `src/shotforge/app/services/` 添加 Web/API service
