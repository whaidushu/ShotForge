# ShotForge_BD 与字节 JD 第 4 点能力映射

目标：把 ShotForge 从 AI 视频 Agent POC 改造成更能展示 AI Agent Harness 工程实践的项目。这个分支重点对齐“方案设计与技术实现”里的工程链路能力：

> 模型选型、工程链路（推理/微调/RAG/Agent/Skill/MCP/安全）、效果评估体系及上线路径。

## 能力映射

| JD 关键词 | ShotForge_BD 对应实现 |
| --- | --- |
| Agent Harness | `AgentHarnessRuntime` 统一编排 Agent 执行、上下文构建、工具记录和策略元数据 |
| Context Engineering | `ContextBuilder` 输出 `ContextBundle`，按来源、优先级、窗口预算组织上下文 |
| Tool Orchestration | `SkillRegistry` 支持 `SkillSpec`、权限域、风险等级和 `ToolCallRecord` |
| State Management | `ProjectState` 贯穿 Design / Evaluation / Redesign / Version / Trace |
| RAG / Knowledge | `KnowledgeBase` 作为轻量知识检索源，并进入 `ContextBundle` |
| Memory | `InMemoryStore` 提供可替换的项目记忆接口 |
| MCP | `MockMCPClient` 提供 list/call tool 协议骨架，后续可替换真实 MCP client |
| Sandbox / 安全 | `SandboxPolicy` / `LocalSandbox` 表达 dry-run、文件、网络和运行时策略 |
| 效果评估体系 | `EvaluationRubric`、`EvaluationReport`、`Issue`、`ScoreDelta`、`RegressionCheck` |
| 上线路径 | Snapshot、VersionDiff、TraceLog、CLI/Web/API、Provider 抽象 |

## 当前分支新增内容

```text
src/shotforge/core/
  harness_runtime.py
  run_context.py
  execution_policy.py
  tool_call.py
  memory.py

src/shotforge/infra/
  skills/
  mcp/
  sandbox/
```

这些模块暂时以本地 mock / dry-run 为主，目的是先把生产级 Agent Harness 的接口和边界做清楚，再接真实服务。

## 可讲述的工程链路

```text
LangGraph Workflow
  -> AgentHarnessRuntime
  -> RunContext
  -> ContextBuilder / ContextBundle
  -> Agent
  -> SkillRegistry / ToolCallRecord
  -> ProjectState / TraceLog
  -> Evaluation / Regression / VersionDiff
```

这个结构比“多个 Agent 顺序调用”更贴近生产级 Harness：每一步都有上下文来源、工具协议、执行策略、状态追踪和效果评估。

## 后续可扩展方向

- 把 `MockMCPClient` 替换为真实 MCP client。
- 把 `InMemoryStore` 替换为 Redis / SQLite / Vector DB。
- 给 `ExecutionPolicy` 增加按工具和 Agent 的权限白名单。
- 让 `SandboxPolicy` 接真实隔离执行环境。
- 把 `ContextBundle` 的 token 估算换成真实 tokenizer。
- 给每个 Agent 增加 retry、timeout、fallback provider 策略。
