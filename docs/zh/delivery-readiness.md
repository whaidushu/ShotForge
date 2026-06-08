# 交付就绪度

ShotForge 会为每次 design run 生成 `DeliveryReadinessReport`。

这个报告用于说明当前 run 哪些内容已经可交付，哪些本地 provider 配置还不完整，以及生产化前还需要补什么。

## 检查项

当前 gates 包括：

- `state_schema`：intent、shots、prompts、versioned state 是否存在。
- `context_observability`：是否记录 agent context 快照。
- `tool_policy`：工具调用是否有状态和权限范围。
- `state_transition_audit`：状态变更和 invariant 是否记录。
- `context_safety`：context digest 和 redaction 元数据是否存在。
- `mcp_capability`：MCP-like 工具是否暴露。
- `memory_strategy`：memory 是否可用或可 promoted。
- `solution_architecture`：run 是否有架构摘要。
- `export_contract`：JSON/CSV/Markdown 导出是否注册。
- `provider_strategy`：是否有真实 provider profile，还是只有 local test profile。
- `evaluation_loop`：是否存在评估、重写或验证证据。

## 交付物

普通 run 可以产生：

- ProjectState JSON package
- Storyboard CSV package
- Markdown production brief
- Runtime audit trace
- Run architecture summary
- Delivery readiness report

Full-loop run 还可能包含：

- evaluation report 和 issue list
- correction plans 和 patches
- version diff 和 redesign evidence
- verification report

## 检查方式

```text
GET /api/runs/{run_id}/harness
GET /api/runs/{run_id}/readiness
```

CLI：

```bash
shotforge audit data/runs/{run_id}/package.json
```

## 生产边界

该报告不声称项目已经生产就绪，只是显式标出：

- local test provider 说明真实 provider 凭证和服务 readiness 仍需要配置
- 本地文件存储说明生产持久化仍需要补齐
- 本地沙箱策略说明容器隔离仍需要增强
- 静态知识规则说明部署特定知识覆盖仍需要补充
