# 配置

ShotForge 可以使用确定性的开发 provider，也可以连接本地或远程模型服务。配置可以来自
`.env`、provider profile 和 Web 配置页。

## 环境文件

从示例文件开始：

```powershell
copy .env.example .env
```

常用配置：

```text
SHOTFORGE_LLM_PROVIDER=ollama
SHOTFORGE_LLM_MODEL=qwen2.5:7b
SHOTFORGE_LLM_BASE_URL=http://localhost:11434/v1
SHOTFORGE_EVALUATOR_MODE=hybrid
SHOTFORGE_VIDEO_PROVIDER=comfyui
SHOTFORGE_COMFYUI_BASE_URL=http://127.0.0.1:8188
```

支持的环境变量以 `.env.example` 为准。

## Provider Profile

Provider profile 把一次可运行配置需要的设置收在一起：

- LLM/Judge provider
- 视频 provider
- 视觉观察 provider
- ComfyUI 地址和 workflow ID
- 模型名称和 OpenAI-compatible base URL

这些配置可以在 Web 配置页维护，也可以由 API 和 CLI 使用。Web 端会把
LLM/Judge、Video、Visual Observer 分开配置，便于用户分别测试服务。

## 预检

真实生成前先做预检：

```powershell
shotforge doctor --deep
```

Web 端也会检查：

- 模型服务是否可达
- ComfyUI 是否启动
- 选择的 workflow 是否存在
- provider profile 是否完整
- 输出目录和产物路径是否可用

## ComfyUI Workflow

ShotForge 使用 API-format ComfyUI workflow。项目可以发现内置 workflow，也可以发现
用户本地 workflow。使用本地 workflow 时，建议先在 provider profile 中保存选择，再运行完整生成。
