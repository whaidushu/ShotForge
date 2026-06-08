# Agent 基础设施运行时

ShotForge 包含一个最小 Agent Infra runtime 层，让 agent 执行过程可见、可受策略约束、可扩展，而不是把 MCP、sandbox、memory、skills 只停留在概念上。

## 组件

| 组件 | 当前能力 | 后续边界 | 代码 |
|---|---|---|---|
| Agent Catalog | 记录 agent 角色、输入输出、依赖和技能 | 可扩展为可视化拓扑 | `AgentCatalog` |
| Runtime Policy | 捕获执行和沙箱策略 | 可做项目级策略 | `ExecutionPolicy`, `SandboxPolicy` |
| MCP Adapter | 本地 MCP-like 工具/资源适配 | 可替换为正式 MCP transport | `LocalMCPAdapter` |
| Memory | JSONL 本地记忆 | 可替换为向量库或数据库 | `LocalMemoryStore` |
| Sandbox | 本地策略门禁 | 可替换为容器沙箱 | `LocalSandboxRunner` |
| Agent Contracts | 校验 pre/post condition | 可扩展为审批和修复策略 | `AgentContractReport` |

## 运行流

```text
agent starts
-> validate preconditions
-> build context
-> record memory hits / tools / policies
-> execute agent
-> validate postconditions
-> record transition and audit evidence
```

## 为什么重要

视频生成工作流不仅要能运行，还要能解释：

- 用了哪些上下文。
- 调了哪些工具。
- 哪些策略允许或拒绝操作。
- 状态如何变化。
- 失败时如何定位。
- 后续如何替换真实工具、沙箱和记忆系统。

## Runtime Scope

该层覆盖：

- context engineering
- tool orchestration
- state management
- skill 和 MCP-style extension boundaries
- sandbox policy
- memory 和 knowledge retrieval 基础
- safety policy
- 从本地 prototype 到生产化 hardening 的稳定交付路径

## 测试

核心测试见：

```text
tests/test_agent_infra_runtime.py
```
