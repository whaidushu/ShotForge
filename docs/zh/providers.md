# Provider

ShotForge 会把 provider 类型分开，这样一次 run 可以分别使用不同服务完成文本推理、
视频渲染和视觉检查。

## Provider 类型

- **LLM/Judge**：生成提示词、修订提示词、执行 LLM-as-judge 评分。
- **Video**：通过本地或外部渲染器生成 MP4。
- **Visual Observer**：检查生成视频的帧和序列。

## 支持路径

| 类型 | Provider 示例 | 常见用途 |
| --- | --- | --- |
| LLM/Judge | Ollama、vLLM、OpenAI-compatible APIs | 本地或 API 文本推理 |
| Video | ComfyUI、test provider | 真实本地渲染或确定性测试 |
| Visual Observer | prompt-proxy、OpenAI-compatible vision、Ollama vision、vLLM VLM | 观察生成帧 |

test provider 适合开发和 CI。真实生成时，建议配置真实 LLM/Judge provider 和
ComfyUI 这类视频 provider。

## ComfyUI

ComfyUI 集成需要：

- 正在运行的 ComfyUI server
- API-format workflow
- provider profile 中选择的 workflow ID
- ShotForge 能解析的输出路径

可以在 Web 配置页搜索 workflow、选择 workflow，并在完整生成前运行 preflight。

## 视觉观察

视觉观察 provider 会检查抽取出来的视频帧，并生成 observation。评估器会把 observation
和用户请求对齐，检查必须出现的物体、地点、天气、动作，以及帧与帧之间的一致性。
