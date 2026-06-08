# 能力目录

ShotForge 通过能力目录暴露当前系统能力：

```text
GET /api/capabilities
```

能力目录用于快速了解项目已经实现了什么、哪些 provider 可用、有哪些导出格式和 API 路由，而不需要直接阅读源码。

## 主要内容

- `agents`：已注册 agent 和职责。
- `providers`：LLM/Judge、视频生成、视觉观察 provider。
- `infra`：MCP-style、sandbox、memory、knowledge 能力。
- `exports`：支持的导出格式。
- `api_routes`：主要 Web/API 路由。
- `playbooks`：可复用场景和质量规则资产。

## Provider 目录

Provider 目录会包含可用 provider 和计划中的 provider。用户默认路径不应使用 local test provider；真实生成前应通过 preflight 检查 readiness。

## 用途

- 快速查看系统边界。
- 检查 Web/API/CLI 是否暴露一致能力。
- 为后续 provider、exporter、observer 扩展提供目录化入口。
