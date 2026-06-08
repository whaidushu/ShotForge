# 架构概览

## 端到端流程

```text
用户创意
-> Provider Profile
-> ProjectState
-> 设计包
-> Prompt / Template Package
-> 视频 Provider 产物
-> 帧抽取与视觉观察
-> 分层评估
-> 修正计划
-> 重新生成
-> 版本 Diff / 运行历史
-> 导出与交付文件
```

## 核心运行时

| 模块 | 代码 | 作用 |
|---|---|---|
| 状态模型 | `ProjectState` | 承载创意、镜头、prompt、评估、产物和导出 |
| Agent 编排 | `workflows/` | LangGraph 工作流 |
| Provider 服务 | `ProviderService`, `ProviderRuntimeService` | 配置 LLM、视频和观察 provider |
| ComfyUI 工作流 | `ComfyUIWorkflowService` | 搜索内置和本地 API-format workflow |
| 视觉观察 | `VideoObservationService` | 抽帧并运行观察器 |
| 评估 | evaluator registry | 物理、连续性、静态和 LLM/Judge 信号 |
| 版本 | `VersionManager`, `VersionDiffBuilder` | 快照和字段级 diff |
| 运行时证据 | `AgentHarnessRuntime` | 上下文、工具、策略、沙箱、记忆 |

## Provider 表面

| 表面 | 当前实现 | 职责 |
|---|---|---|
| LLM/Judge | local test, Ollama, vLLM, OpenAI-compatible | 文本推理、prompt 评估和重写 |
| 视频生成 | local test, ComfyUI | 生成视频产物 |
| 视觉观察 | prompt-proxy, OpenAI vision, Ollama vision, vLLM VLM | 检查抽帧后的可见事实 |

## 公开接口

```text
POST /api/runs
GET /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/workbench
GET /api/runs/{run_id}/generation-artifacts
GET /api/runs/{run_id}/harness
GET /api/runs/{run_id}/readiness
GET /api/runs/{run_id}/versions
GET /api/runs/{run_id}/export/{format}
GET /api/provider-profiles
POST /api/provider-profiles
GET /api/observer-providers
POST /api/preflight
GET /api/comfyui/workflows
GET /api/capabilities
```

## 生成产物

每次运行会在 `data/runs/{run_id}` 下生成包、trace、summary、评估报告、prompt、workflow、视频、帧和版本信息。

## 生产边界

当前项目是本地优先。生产化还需要补充部署打包、认证、多租户、持久存储、可观测性、配额控制和更强沙箱隔离。
