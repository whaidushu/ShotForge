# 工程线

工程线关注 ShotForge 的运行时、状态、扩展边界和可验证性。

## 定位

ShotForge 不只是生成 prompt。工程核心是让一次视频生产运行具备可追踪、可评估、可重放、可导出的结构。

## 需要可检查的内容

- 状态是否清晰。
- Agent 是否按图执行。
- Context 是否经过构造和预算控制。
- Tool 调用是否有策略和记录。
- Provider 是否可替换。
- Evaluation 是否能产出结构化问题。
- Correction 是否能回写到 prompt/template package。
- Version diff 是否能解释迭代变化。
- Export 是否能支持交付。

## 核心模块

```text
core/project_state.py       类型化状态
workflows/                  LangGraph 工作流
agents/                     设计、评估、修正、导出 agents
app/services/               Web/API 共享服务
generators/                 视频 provider
llm/                        LLM/Judge provider
observation/                抽帧、观察器、序列观察
evaluators/                 评估器与 signal aggregation
infra/                      MCP-style、memory、sandbox
exporters/                  JSON/CSV/Markdown/trace 等导出
```

## 工程边界

- Provider 只通过协议和 registry 接入。
- Runtime state 通过 Pydantic 模型传递。
- Web/API/CLI 共享 service 层。
- Local test provider 用于 CI 和确定性测试。
- ComfyUI、Ollama、vLLM 等真实服务通过配置启用。

## 评审信号

一个好的工程评审应该能看到：

- 运行链路不是散脚本。
- Provider 配置和 readiness 明确。
- 评估不是只看文本，而能接入视频观察。
- 产物、版本、trace 和 export 都能落盘。
- 未来接入更多模型时不需要重写核心 workflow。
