# 变更日志

## 2026-06-09 公开文档收敛

这一轮把公开文档收敛成更轻量的开源项目结构：

- 快速开始
- 配置
- 架构
- Provider
- 评估
- API 参考
- 开发
- 变更日志

偏面试评审、内部规划和设计探索的材料从公开 docs 中移除，并归档到本地私有目录。

## 2026-06-01 Runtime Strategy And Public Documentation

这一阶段加深 runtime strategy，并补充公开的架构、交付和 provider 选择文档。

### Runtime Strategy

- 增加本地 JSONL memory 的治理策略。
- 增加 workflow gate metadata，覆盖工具失败、memory、sandbox、MCP、observation 和 export。
- 增加 sandbox strategy records。
- 增加 MCP access policy 和 access record。
- 通过 runtime audit 和 CLI audit 暴露 memory、sandbox 和 MCP 证据。

### Public Documentation

- 增加公开 architecture、runtime audit、delivery readiness 和 provider selection 文档。
- 增加 model selection matrix。
- 增加 project spine 和 workbench layer 文档，对齐当前 workbench flow。

### Verification

- 当前验证：`ruff check src tests` 和 `pytest`。

## 2026-05-31 Delivery Chain Consolidation

这一阶段把 ShotForge 从概念框架推进成可运行的本地交付链路。

### Product Flow

- 增加 FastAPI Web product shell，并拆分 workflow/configuration 页面。
- 增加 provider profile 管理。
- 增加 service preflight checks。
- 增加 local readiness testing。
- 增加 run progress、recent run history、prompt changes、generated artifacts 和 per-iteration artifact folders。

### Real Local Provider Path

- 增加 Ollama、vLLM、OpenAI-compatible LLM provider。
- 增加 ComfyUI provider execution、workflow discovery、API-format validation 和 video artifact resolution。
- 增加 bundled ComfyUI workflow 和可读产物命名。
- 增加 API/Web 对用户本地 ComfyUI workflow 的支持。

### Evaluation And Iteration

- 增加从具体视觉事实到抽象表达的分层评估：
  - `physical_effect`
  - `frame_consistency`
  - `style_color`
  - `emotion_atmosphere`
  - `prompt_execution`
- 增加 physical target extraction。
- 增加 prompt correction operations。
- 增加 LLM evaluator JSON repair/fallback。
- 增加 convergence metadata、prompt diffs、correction plans、version diffs、score deltas 和 regression checks。

### Visual Observation

- 增加 `shotforge.observation`。
- 增加 frame extraction、frame observers、sequence observation 和 `VideoObservationService`。
- 增加 observer providers：`prompt-proxy`、`openai-vision`、`ollama-vision`、`vllm-vlm`。

### Application Architecture

- 将 Web/API 逻辑拆到共享 services。
- 增加 structured package 和 observation schemas。
- 增加 MCP、sandbox、provider protocol 和 generator client 扩展边界。
- 增加 UI static asset structure。
