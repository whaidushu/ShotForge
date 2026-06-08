# 运行时审计 API

ShotForge 通过以下接口暴露 run 级运行时证据：

```text
GET /api/runs/{run_id}/harness
```

该接口只读，用于调试、评审和架构检查，补充产品级 workbench API。

返回内容包括：

- `contexts`：每个 agent 的上下文快照。
- `tool_calls`：`SkillRegistry` 记录的工具执行。
- `state_transitions`：每个 agent 前后的状态摘要和 invariant 状态。
- `agent_topology`：本次运行的 agent 节点和边。
- `policies`：执行策略、MCP-style 工具、沙箱策略和记忆摘要。
- `state_summary`：trace、knowledge、memory、evaluation、correction、generation、export 计数。
- `solution`：当前 run 的架构元数据。
- `readiness`：交付检查、下一步动作、交付物和风险。

示例：

```bash
curl http://127.0.0.1:8000/api/runs/{run_id}/harness
```

当需要不打开源码就检查创意如何经过 agent、context、工具策略、provider 边界、状态变更和导出就绪度时，使用该接口。
