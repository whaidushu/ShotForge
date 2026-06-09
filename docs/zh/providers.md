# Provider

ShotForge 为文本推理、视频渲染和视觉观察分别定义 provider 合同。这样每类服务都可以替换，
而不需要改核心 workflow state。

## Provider 角色

| 角色 | 职责 | 主要配置 |
| --- | --- | --- |
| LLM/Judge | 提示词生成、提示词修订、LLM-based scoring | provider id、model、base URL、API key、evaluator mode |
| Video | 将 prompt package 渲染成视频 artifact | provider id、service URL、workflow id、渲染参数 |
| Visual Observer | 检查抽取帧并生成视觉 observation | provider id、model、base URL、API key、frame sampling |

## Generator Provider 合同

Generator provider 实现 `src/shotforge/generators/base.py` 中的协议：

| 方法 | 用途 |
| --- | --- |
| `generate(state)` | 从 `ProjectState` 渲染 artifact。 |
| `supports_real_generation()` | 区分真实可运行 provider 和测试/规划 provider。 |
| `estimate_cost(state)` | 调用前返回成本估算。 |
| `capabilities()` | 描述 modality、duration、aspect ratio、batch 和 metadata 支持。 |

`GeneratedResult` 保存：

- provider id
- generation status
- generated shots
- artifact references
- observation report id
- provider metadata

每个 `GeneratedShotResult` 保存：

- `shot_id`
- `prompt_id`
- video URI/path
- duration
- detected elements
- motion/audio summaries
- quality signals
- frame observations
- artifact metadata

## 可运行视频路径

当前真实可运行的视频路径是 ComfyUI-backed provider。它需要：

- 可访问的视频服务
- API-format workflow
- 选中的 workflow id
- ShotForge 能解析的输出文件节点
- 与 workflow 兼容的渲染参数

provider 会为每个 shot 写入：

- prompt text
- prompt JSON
- workflow API payload
- video artifact

这些文件通过 `/api/runs/{run_id}/generation-artifacts` 和
`/api/runs/{run_id}/artifacts/...` 暴露。

## 规划中或外部 Provider

Generator registry 中也包含常见视频模型集成的 planned provider adapter。planned provider
用于展示接口边界，但只有实现和凭据补齐后才可运行。选择不可运行 provider 时，preflight 会返回失败。

## LLM/Judge Provider

LLM/Judge provider 用于：

- design 和 prompt generation
- LLM-based storyboard/prompt scoring
- prompt redesign 和 correction

provider profile 保存 provider id、model name、base URL 和可选 API key。evaluator mode
决定 evaluator registry 的构建方式：

| Mode | 行为 |
| --- | --- |
| `mock` | 只使用确定性/测试 evaluator |
| `llm` | 使用 LLM-based judge evaluator |
| `hybrid` | 确定性检查 + LLM judge |

## Visual Observer Provider

Visual observer provider 检查抽取帧并返回结构化 observation。provider catalog 暴露：

- `provider_id`
- display name
- provider type
- availability
- 是否需要 model/base URL/API key
- default hints
- description

Observation 会被 physical-effect 和 consistency evaluator 使用，用来比较实际帧和目标要求。

## Prompt Proxy Observer

prompt-proxy observer 是开发 fallback。它从 prompt/storyboard 文本推导 observation，而不是检查真实像素。
它适合测试和 UI smoke check；真实视觉检查需要配置 VLM provider。

## Provider Preflight

Preflight 会检查一个 provider profile，并返回状态：

- `passed`：必需服务和 workflow 检查通过
- `warning`：配置可用于有限路径，但不完全是真实链路
- `failed`：必需服务、provider、workflow、model 或 credential 缺失

检查记录形如：

```json
{
  "check_id": "comfyui_workflow",
  "label": "ComfyUI workflow",
  "status": "passed",
  "detail": "<workflow-id> / api / 42 nodes"
}
```

## 添加 Provider

1. 实现 provider contract。
2. 在对应 registry 中注册。
3. 如果需要用户配置，增加 profile 字段。
4. 为必需服务、凭据、模型或文件增加 preflight 检查。
5. 为 provider contract 和失败模式增加测试。
