# 本地部署

ShotForge 当前是本地优先项目，适合在开发机上做工作流验证、provider 测试和演示。

## 安装

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

需要显式本地路径时复制环境文件：

```bash
copy .env.example .env
```

默认运行数据写入 `data/`，该目录不提交。

## CLI 验证

```bash
shotforge design "A neon train crossing a desert at sunrise" --language en
shotforge doctor
shotforge doctor --deep
shotforge capabilities
```

`doctor --deep` 会检查默认 provider profile，包括 LLM/Judge、ComfyUI、workflow、本地 workflow 目录和 visual observer。它不会替用户启动服务，只会说明缺少哪个 URL、模型或路径。

## Provider 设置

ShotForge 把模型服务拆成三类：

- **LLM/Judge provider**：prompt 评估和重写。
- **Video provider**：渲染视频产物。
- **Visual observer provider**：检查视频帧里实际出现了什么。

推荐在 Web 配置页或 provider profile 中保存 URL、模型名和 workflow id。API 请求里只传 `provider_profile_id`。

## 常见本地服务

- Ollama：适合本地 LLM/Judge 或 vision observer。
- vLLM：适合本地或私有高吞吐 OpenAI-compatible 服务。
- ComfyUI：适合本地视频生成和 workflow 控制。

详细模型下载和服务启动命令应只放在部署文档中，不放 README 主入口。

## ComfyUI 工作流

ShotForge 支持：

- 内置 workflow，例如 `wan2_2_i2v_empty_start`。
- 用户本地 workflow 目录搜索。
- 直接指定 API-format JSON 文件。

只有 API-format workflow 可以发送到 `/prompt`。普通 UI graph 需要先在 ComfyUI 中保存为 API 格式。

## Web 启动

```bash
python -m uvicorn shotforge.app.web.app:app --reload --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

不要直接打开 `src/shotforge/templates/index.html`，Web UI 必须通过 FastAPI/Jinja 渲染。

## 存储结构

```text
data/
  runs/{run_id}/
    package.json
    package.csv
    package.md
    manifest.json
    trace.json
    run_summary.md
    evaluation.csv
  versions/{project_id}/
  knowledge_base.json
  memory.jsonl
```

## 生产化边界

生产部署仍需要补充 Docker/Compose、认证、多租户、持久存储、可观测性、配额控制、正式 MCP transport 和更强沙箱隔离。
