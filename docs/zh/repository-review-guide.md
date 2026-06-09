# 仓库评审指南

这份文档用于帮助评审者在很短时间内理解 ShotForge。

## 30 秒理解

ShotForge 是一个构建在可审计 Agent Harness 运行时之上的 AI 视频工作台。

它有两个连接在一起的架构层：

- **Agent Harness 层**：负责工作流架构、类型化状态、可追踪性、版本管理、评估、Memory、MCP-style 访问、Sandbox 策略和 provider 扩展。
- **AI 视频工作台层**：负责面向用户的短视频生产流程，包括 provider 配置、运行历史、产物查看、提示词变更、评估、版本对比和导出。

## 优先阅读

1. `README.md`：项目定位与快速开始。
2. `project-spine-and-demo-path.md`：项目主线和演示路径。
3. `architecture-overview.md`：运行时、provider、API 和产物地图。
4. `video-workbench-layer.md`：当前产品工作流和后续方向。
5. `src/shotforge/core/project_state.py`：核心状态模型。
6. `src/shotforge/workflows/`：LangGraph 工作流定义。
7. `tests/`：行为覆盖。

## 项目为什么存在

AI 视频生成不只是一次模型调用。复杂创意输出更像一个工程闭环：

```text
plan -> generate -> observe -> evaluate -> correct -> version -> converge -> export
```

ShotForge 把这个闭环做成用户可操作的工作台，并在底层保留可审计的 Agent Harness 运行时。

## 工程亮点

- 跨流程共享的 Pydantic 状态模型。
- LangGraph 编排。
- LLM/Judge、视频生成、视觉观察三类 provider 表面。
- 分层评估和修正计划。
- 版本快照、版本 diff、提示词变更卡片和运行历史。
- Trace log 和 runtime audit API。
- JSON、CSV、Markdown、manifest、trace、run summary、evaluation report 导出。
- 中英文输出。
- MCP-style、沙箱、记忆、知识资产和外部视频模型的扩展边界。

## 产品亮点

- Web 工作台支持从一个创意开始生成视频工作流。
- Provider profile 配置和 preflight 检查。
- ComfyUI workflow 搜索和产物链接。
- Storyboard 与 prompt package 输出。
- 评估和迭代表面。
- 版本链和 prompt diff。
- 可导出的交付包。

## 运行方式

```powershell
pip install -e ".[dev]"
shotforge design "A cyber cat chases a glowing drone across rainy Shanghai rooftops"
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
uvicorn shotforge.app.web.app:app --reload
```

## 重点检查

- 模糊创意如何变成结构化状态。
- Provider 如何配置和预检。
- Prompt、视频、观察、评估之间如何连接。
- 版本 diff 如何解释迭代变化。
- 产物和导出如何支持交付，而不仅是页面展示。
