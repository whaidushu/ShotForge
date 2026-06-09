# 架构

ShotForge 包含两层：

- **AI 视频工作台**：面向用户的 Web/API/CLI 表面，用于创建 run、配置 provider、
  查看提示词和产物、评估输出、比较版本并导出交付物。
- **Agent Harness Runtime**：可检查的执行层，用于类型化状态、上下文构建、agent 契约、
  工具调用、provider 边界、评估、trace 和版本快照。

## Run 流程

```text
idea
-> provider profile
-> ProjectState
-> design package
-> prompt/template package
-> video provider artifact
-> frame extraction and visual observation
-> layered evaluation
-> correction plan
-> regenerated package/artifact
-> version diff
-> export
```

## 主要模块

```text
src/shotforge/
  app/          CLI 和 FastAPI Web 入口
  agents/       design、evaluation、correction、structuring、export agents
  core/         ProjectState、context、trace、versioning、rubrics
  evaluators/   静态评估和 provider-backed 评估
  generators/   测试和真实视频生成 provider
  observation/  抽帧和视觉观察
  workflows/    LangGraph workflow 定义
```

## 状态与产物

`ProjectState` 是 workflow 共享的类型化状态对象。运行产物存放在
`data/runs/{run_id}`，方便把提示词、视频、观察、评估、版本、trace 和导出文件放在一起检查。

## 扩展边界

当前主要扩展点包括：

- LLM/Judge provider
- 视频生成 provider
- 视觉观察 provider
- 评估 rubric
- correction agent
- exporter
- workflow node
