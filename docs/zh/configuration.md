# 配置

ShotForge 可以使用内置测试 provider，也可以连接本地或远程模型服务。配置来源有三类：

1. `.env`，由 `shotforge.config.Settings` 加载。
2. `data/provider_profiles.json` 中保存的 provider profiles。
3. Web 表单或 API payload 中的请求级覆盖。

正常运行时优先使用 provider profile。自动化调用可以通过请求 payload 覆盖 profile 字段。

## 环境文件

从示例文件开始：

```powershell
copy .env.example .env
```

公开示例使用占位符，真实 secret 只放在本地 `.env`。

```text
SHOTFORGE_APP_NAME=ShotForge
SHOTFORGE_STORAGE_ROOT=data
SHOTFORGE_RUNS_DIR=data/runs
SHOTFORGE_VERSIONS_DIR=data/versions
SHOTFORGE_PROVIDER_PROFILES_PATH=data/provider_profiles.json

SHOTFORGE_LLM_PROVIDER=<llm-provider-id>
SHOTFORGE_LLM_MODEL=<model-name>
SHOTFORGE_LLM_BASE_URL=<openai-compatible-base-url>
SHOTFORGE_LLM_API_KEY=<api-key-if-required>
SHOTFORGE_EVALUATOR_MODE=hybrid

SHOTFORGE_COMFYUI_ENABLED=true
SHOTFORGE_COMFYUI_BASE_URL=<video-service-base-url>
SHOTFORGE_COMFYUI_WORKFLOWS_DIR=<path-to-api-workflows>
SHOTFORGE_COMFYUI_WORKFLOW_ID=<workflow-id>

SHOTFORGE_OBSERVER_PROVIDER=<observer-provider-id>
SHOTFORGE_VLM_MODEL=<vision-model-name>
SHOTFORGE_VLM_BASE_URL=<vision-base-url>
SHOTFORGE_VLM_API_KEY=<api-key-if-required>
```

## 存储配置

| 变量 | 用途 |
| --- | --- |
| `SHOTFORGE_STORAGE_ROOT` | 基础数据目录。 |
| `SHOTFORGE_RUNS_DIR` | run package 和生成 artifact。 |
| `SHOTFORGE_VERSIONS_DIR` | 版本快照。 |
| `SHOTFORGE_KNOWLEDGE_BASE_PATH` | 本地知识库 JSON。 |
| `SHOTFORGE_MEMORY_STORE_PATH` | 本地 JSONL memory store。 |
| `SHOTFORGE_PROVIDER_PROFILES_PATH` | provider profile JSON 文件。 |

应用启动时会创建需要的目录。

## LLM/Judge 配置

| 变量 | 用途 |
| --- | --- |
| `SHOTFORGE_LLM_PROVIDER` | 用于提示词生成和 judge 调用的 provider id。 |
| `SHOTFORGE_LLM_MODEL` | provider 能识别的模型名。 |
| `SHOTFORGE_LLM_BASE_URL` | API-compatible provider 的 base URL。 |
| `SHOTFORGE_LLM_API_KEY` | 可选 API key。 |
| `SHOTFORGE_LLM_TEMPERATURE` | 采样温度。 |
| `SHOTFORGE_LLM_TIMEOUT_SECONDS` | 请求超时时间。 |
| `SHOTFORGE_EVALUATOR_MODE` | `mock`、`llm` 或 `hybrid`。 |

当需要确定性检查加 judge 模型时，使用 `hybrid`。

## 视频 Provider 配置

| 变量 | 用途 |
| --- | --- |
| `SHOTFORGE_COMFYUI_ENABLED` | 启用 ComfyUI-backed 视频路径。 |
| `SHOTFORGE_COMFYUI_BASE_URL` | 视频服务 base URL。 |
| `SHOTFORGE_COMFYUI_WORKFLOWS_DIR` | 本地 workflow 发现目录。 |
| `SHOTFORGE_COMFYUI_WORKFLOW_ID` | 选中的 API-format workflow id。 |
| `SHOTFORGE_COMFYUI_TIMEOUT_SECONDS` | 渲染请求超时。 |
| `SHOTFORGE_COMFYUI_WIDTH` | 渲染宽度。 |
| `SHOTFORGE_COMFYUI_HEIGHT` | 渲染高度。 |
| `SHOTFORGE_COMFYUI_LENGTH` | 帧数或 provider-specific length 参数。 |
| `SHOTFORGE_COMFYUI_FPS` | 目标帧率。 |
| `SHOTFORGE_COMFYUI_MAX_SHOTS` | 本地 run 的 shot 上限；`0` 表示不显式限制。 |

## 视觉观察配置

| 变量 | 用途 |
| --- | --- |
| `SHOTFORGE_OBSERVER_PROVIDER` | 视觉观察 provider id。 |
| `SHOTFORGE_VLM_MODEL` | 视觉模型名。 |
| `SHOTFORGE_VLM_BASE_URL` | 本地或 API-compatible VLM base URL。 |
| `SHOTFORGE_VLM_API_KEY` | 可选 API key。 |
| `SHOTFORGE_VLM_FRAME_SAMPLE_COUNT` | 每个 shot 采样帧数，范围 1-16。 |
| `SHOTFORGE_VLM_CONFIDENCE_THRESHOLD` | observation/evaluation 使用的置信度阈值。 |
| `SHOTFORGE_VLM_REQUIRE_JSON` | 支持时要求 VLM 返回 JSON。 |
| `SHOTFORGE_VLM_TIMEOUT_SECONDS` | 帧观察超时时间。 |

## Provider Profile

Provider profile 默认存放在 `data/provider_profiles.json`。一个 profile 会包含：

- LLM/Judge provider 设置
- 视频 provider 设置
- 视觉观察 provider 设置
- workflow 选择
- 渲染参数
- 可选 metadata

API 响应会脱敏 secret。`public_dict()` 返回 `has_llm_api_key` 和 `has_vlm_api_key`，
不会返回明文 key。

示例 profile payload：

```json
{
  "profile_id": "local-profile",
  "name": "Local profile",
  "llm_provider_id": "<llm-provider-id>",
  "llm_model": "<model-name>",
  "llm_base_url": "<base-url>",
  "llm_api_key": "",
  "evaluator_mode": "hybrid",
  "generator_provider_id": "<video-provider-id>",
  "comfyui_base_url": "<video-service-base-url>",
  "comfyui_workflows_dir": "<workflow-directory>",
  "comfyui_workflow_id": "<workflow-id>",
  "comfyui_width": 320,
  "comfyui_height": 320,
  "comfyui_length": 9,
  "comfyui_fps": 8.0,
  "comfyui_max_shots": 0,
  "observer_provider_id": "<observer-provider-id>",
  "vlm_model": "<vision-model-name>",
  "vlm_base_url": "<vision-base-url>",
  "vlm_api_key": "",
  "vlm_frame_sample_count": 4,
  "vlm_confidence_threshold": 0.65,
  "vlm_require_json": true
}
```

通过以下接口保存：

```text
POST /api/provider-profiles
```

## 预检

真实 full generation 前先运行：

```powershell
shotforge doctor --deep
```

或：

```text
POST /api/preflight
```

预检覆盖：

- LLM provider 选择
- 必需模型名
- 必要 API key
- 配置 base URL 时的 LLM server `/models` 可达性
- 视频 provider 支持状态
- 视频服务可用性
- 选中 workflow 的发现和 callability
- workflow 目录是否存在
- 视觉观察 provider 选择
- VLM 模型、base URL、API key 和 server 状态

## Workflow 发现

ShotForge 使用 API-format workflow 做视频生成。workflow discovery API 返回：

- 内置 workflow
- 配置目录下发现的本地 workflow
- 缺失目录或非法 workflow 文件的 warning
- `callable` 状态
- workflow id、source、format、node count 和 path

接口：

```text
GET /api/comfyui/workflows?root=<workflow-directory>
```

## 配置生效顺序

创建 run 时，最终配置按以下顺序构建：

1. 加载默认 settings
2. 有保存的 provider profile 时读取默认 profile
3. 从 Web/API payload 构建 profile
4. 在 scoped runtime context 中应用 profile
5. 将 provider metadata 记录到 `ProjectState.metadata`

这样每次 run 都可以从保存的 package 和 profile metadata 中复盘。
