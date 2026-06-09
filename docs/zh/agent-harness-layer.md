# Agent Harness 层

Agent Harness 层是 ShotForge 底层可审计运行时，负责体现 AI 系统设计和软件工程深度：类型化状态、上下文构建、Agent 契约、工具编排、Memory、MCP-style 访问、Sandbox 策略、评估、追踪和版本化迭代。

这一层应该保持清晰、可测试、模块化、可解释。

## 定位

ShotForge 是构建在 Agent Harness 层之上的 AI 视频工作台。

底层运行时把一句创意通过显式状态、Agent 节点、评估信号、修正计划、版本快照和导出文件，转成结构化生产任务包。

它的核心价值不是“一句 prompt 生成视频”，而是：

```text
结构化状态 + Agent 编排 + 评估闭环 + 可扩展 provider 边界
```

## 这一层应该让审查者看见什么

- Pydantic 领域建模是否清楚。
- LangGraph 编排是否确定、可测试。
- Agent 执行是否可追踪。
- ContextBuilder 是否承担上下文工程。
- 工具是否通过 registry 编排。
- 本地文件存储是否有版本快照。
- 评估和修正是否是一等工作流步骤。
- generator、evaluator、MCP、sandbox、外部 API 是否有清晰扩展点。
- pipeline、API、i18n、generator、evaluator 是否有测试覆盖。
- context、tool call、MCP tool、sandbox policy、memory hit 是否有运行时证据。
- 迭代是否通过 snapshot、diff、run history 和 export artifact 表达。

## 核心模块

```text
src/shotforge/core/
  project_state.py        状态模型和生产任务包 schema
  context_builder.py      Agent 上下文构建
  knowledge_base.py       轻量知识检索
  rubrics.py              评估规则加载
  trace_log.py            执行链路事件
  version_manager.py      快照持久化
  version_diff.py         版本对比
  convergence_engine.py   迭代停止逻辑
  regression_check.py     回归检测
  harness_runtime.py      context、tool、MCP、sandbox、memory 运行时快照
```

```text
src/shotforge/workflows/
  design_workflow.py
  evaluation_workflow.py
  full_loop_workflow.py
  redesign_workflow.py
  redesign_planning_workflow.py
  iterative_redesign_workflow.py
```

```text
src/shotforge/agents/
  design/
  evaluation/
  correction/
  structuring/
  export/
```

## 运行时边界

Agent Harness 层不应该变成重前端应用。它应该暴露工作台可以使用的能力，但不把 UI 假设塞进核心 workflow。

适合继续补的能力：

- 更稳的状态 schema。
- 更好的 trace 和 version diff API。
- 更多 evaluator 插件。
- 更好的 correction routing。
- Provider 抽象。
- MCP 和 sandbox 接口。
- 更多测试和 fixture。

需要谨慎的方向：

- 把复杂前端逻辑塞进 core workflow。
- 产品 UI 假设泄漏进状态模型。
- 直接绑定单一商业视频模型。
- 让非结构化 prompt 字符串成为唯一事实来源。

## 审查信号

审查者应该能看出：

- 这不是脚本集合。
- 状态转换是显式的。
- 没有真实模型调用也能测试 workflow。
- 在接外部模型前，provider 边界已经设计好。
- 评估和修正是架构的一部分，不是后补功能。

## 下一步运行时里程碑

1. 强化 Agent 之间的类型化契约。
2. 增加 trace viewer API 和紧凑 trace summary。
3. 增加 version diff 和 regression check 的 fixture 测试。
4. 在需要时把 MCP-like adapter 推进到官方 transport。
5. 在需要时把 sandbox 从本地策略检查强化到更强隔离。
