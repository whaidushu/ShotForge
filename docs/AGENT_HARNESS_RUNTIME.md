# Agent Harness Runtime

`AgentHarnessRuntime` 是 ShotForge_BD 的工程化入口。它不替代业务 Agent，而是把 Agent 执行需要的基础设施收束到一个运行时：

- 构建 `RunContext`
- 生成结构化 `ContextBundle`
- 暴露 Skill / MCP / Sandbox 策略
- 写入上下文摘要
- 收集 `SkillRegistry` 的工具调用记录
- 保持 `ProjectState` 作为唯一状态载体

## 执行流

```text
AgentHarness.intent_agent(state)
  -> AgentHarnessRuntime.run_agent()
  -> build_run_context()
  -> context_builder.build_bundle()
  -> intent_agent()
  -> registry.call()
  -> tool_call_records 写回 state.metadata
```

## 为什么这样设计

普通 Demo 往往只证明 Agent 能跑。Harness Runtime 要证明的是：

- Agent 运行的上下文可解释。
- 工具调用可追踪。
- 执行策略可配置。
- 状态变化可复盘。
- 后续接 MCP、Sandbox、Memory 不需要重写业务 Agent。

这对应生产级 Agent 系统从 Demo 到稳定运行时最容易缺失的工程层。
