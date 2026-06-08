# 模型选择矩阵

ShotForge 把 provider 拆成 LLM/Judge、视频生成、视觉观察三类。这样在运行前就能明确质量、延迟、成本、隐私和 readiness 的取舍。

## 选择维度

| 维度 | 关注点 |
|---|---|
| 质量 | prompt 跟随、视觉一致性、物理目标匹配 |
| 延迟 | 首次结果时间和吞吐 |
| 成本 | token、生成、重试成本 |
| 隐私 | prompt、素材、视频是否离开本地 |
| 可靠性 | 失败模式、重试、服务可用性 |
| 集成 | API 稳定性、workflow 支持、产物处理 |
| 治理 | 日志、策略、审计、安全能力 |

## LLM / Judge

| 类型 | 适合场景 | 代价 | ShotForge 表面 |
|---|---|---|---|
| Local test | 确定性测试和 CI | 没有真实推理质量 | `MockLLMProvider` |
| Ollama | 本地和隐私敏感测试 | 受本机硬件限制 | `OllamaProvider` |
| vLLM | 本地或私有高吞吐 | 需要 GPU/服务部署 | `VLLMProvider` |
| OpenAI-compatible | 云端或企业模型接入 | 网络、成本、凭证治理 | `OpenAICompatibleProvider` |

## 视频生成

| 类型 | 适合场景 | 代价 | ShotForge 表面 |
|---|---|---|---|
| Local test | Pipeline、UI、CI 稳定性 | 没有真实视频质量 | `MockGenerator` |
| ComfyUI | 本地生成、workflow 控制 | 需要 GPU 和 workflow 维护 | `ComfyUIProvider` |
| Planned cloud providers | 未来托管视频服务适配 | API 差异、成本、凭证治理 | Provider adapter boundary |

## 视觉观察

| 类型 | 适合场景 | 代价 | ShotForge 表面 |
|---|---|---|---|
| Prompt proxy | 低成本本地回退 | 不能验证真实像素 | `prompt-proxy` |
| OpenAI-compatible vision | 云端视觉检查 | 成本和数据外传 | VLM observer |
| Ollama vision | 本地隐私敏感检查 | 模型质量和延迟不稳定 | VLM observer |
| vLLM VLM | 私有高吞吐视觉检查 | 需要 GPU/服务部署 | VLM observer |

## 选择策略

```text
Stage 1: local test providers
  验证 workflow、state、export 和 audit。

Stage 2: local LLM/Judge
  低成本验证评估和重写。

Stage 3: local or approved video provider
  验证视频产物和观察闭环。

Stage 4: provider benchmark
  比较质量、延迟、成本、重试率和运行风险。

Stage 5: production selection
  基于部署约束确定 provider 组合和准入门槛。
```

## 运行中应记录

- provider profile 名称
- model/provider id
- preflight 结果
- generation artifact 路径
- observation provider id
- evaluation mode
- 成本/延迟元数据
- fallback 或失败原因
