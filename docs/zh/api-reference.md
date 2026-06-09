# API 参考

ShotForge 在 `/api` 下提供本地 FastAPI 接口。调用前先启动 Web 应用：

```powershell
shotforge web --reload
```

默认本地地址：

```text
http://127.0.0.1:8000
```

## 请求约定

- JSON 请求使用 `Content-Type: application/json`。
- `run_id` 对应 `data/runs/{run_id}` 下的本地目录。
- 读取类接口在 run 或 artifact 不存在时返回 `404`。
- provider 或生成失败时通常返回 `503`，`detail` 中尽量给出结构化检查信息。

## 健康检查

### `GET /api/health`

返回应用和存储状态，用于确认服务已启动、配置可加载、存储路径可解析。

关键字段：

| 字段 | 含义 |
| --- | --- |
| `status` | 服务状态，通常为 `ok`。 |
| `storage.storage_root` | 基础存储目录。 |
| `storage.runs_dir_exists` | run 目录是否存在。 |
| `storage.versions_dir_exists` | 版本目录是否存在。 |
| `comfyui.*` | 当前视频服务相关配置。 |
| `observer.*` | 当前视觉观察配置。 |

### `GET /api/capabilities`

返回能力目录，包括 agents、generator providers、LLM providers、API routes、
export formats 和 playbooks。构建配置页或自动化工具时，可以先读这个接口。

## 效果 Demo

### `GET /api/effect-demos`

列出内置效果 demo case。每个条目包含 `case_id`、标题、时长和本地 case 路径。

### `POST /api/effect-demos/{case_id}`

运行固定的 v1/v2/v3 效果 demo case。v1 使用用户原始提示词，v2 使用翻译后的结构化提示词，v3 是基于抽帧观察后的候选补偿版本。对比报告会记录 preservation locks，以及 v3 候选是否被接受或拒绝。

请求体：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `language` | string | `en` | 输出语言，`en` 或 `zh`。 |
| `generator_provider_id` | string | `mock` | 所有生成迭代使用的生成 provider。 |
| `style` | string/null | null | 可选风格覆盖。 |

关键响应字段：

| 字段 | 含义 |
| --- | --- |
| `run_id` | 创建出的 run id。 |
| `case_id` | 效果 case id。 |
| `comparison` | v1/v2/v3 分数变化、目标变化、已修复/未解决/回归目标、preservation locks、候选状态、接受版本和修正计划。 |
| `exports` | 标准 run 导出路径。 |
| `state` | 完整 `ProjectState`。 |

### `GET /api/runs/{run_id}/effect-comparison`

返回已完成效果 demo run 的对比报告。

### `GET /api/effect-demos/{run_id}/comparison`

从 effect-demo API 命名空间读取对比报告的别名。

## 创建 Run

### `POST /api/runs`

创建一次 run，并把导出文件写到 `data/runs/{run_id}`。

最小 design-only 请求：

```http
POST /api/runs
Content-Type: application/json

{
  "idea": "日出时穿越沙漠的霓虹列车",
  "style": "cinematic",
  "language": "zh",
  "duration_seconds": 24
}
```

带评估的 full-loop 请求：

```http
POST /api/runs
Content-Type: application/json

{
  "idea": "一个电影感 AI 视频创意",
  "style": "cinematic",
  "language": "zh",
  "duration_seconds": 24,
  "with_evaluation": true,
  "rubric_id": "baseline_v1",
  "provider_profile_id": "local-profile",
  "provider_profile_name": "Local profile",
  "generator_provider_id": "<video-provider-id>",
  "llm_provider_id": "<llm-provider-id>",
  "llm_model": "<model-name>",
  "llm_base_url": "<openai-compatible-base-url>",
  "observer_provider_id": "<observer-provider-id>"
}
```

带迭代优化的 planning 请求：

```json
{
  "idea": "雨夜城市街道中的产品揭示镜头",
  "language": "zh",
  "with_evaluation": true,
  "with_planning": true,
  "max_iterations": 3
}
```

### Run 请求字段

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `idea` | string | 必填 | 用户创意，至少 2 个字符。 |
| `style` | string | `cinematic` | 视觉风格提示。 |
| `language` | `en` 或 `zh` | `zh` | 控制输出语言。 |
| `duration_seconds` | integer | `24` | 范围：6-180。 |
| `with_evaluation` | boolean | `false` | 是否运行生成和评估。 |
| `with_planning` | boolean | `false` | 是否在评估后运行迭代 redesign。 |
| `rubric_id` | string | `baseline_v1` | 评估 rubric id。 |
| `max_iterations` | integer | `3` | 范围：2-10，planning 模式使用。 |
| `provider_profile_id` | string | profile id | 保存的 profile 标识。 |
| `provider_profile_name` | string | profile name | profile 展示名。 |
| `generator_provider_id` | string | provider id | 视频 provider id。 |
| `llm_provider_id` | string/null | profile value | LLM/Judge provider id。 |
| `llm_model` | string/null | profile value | 所选 LLM provider 使用的模型名。 |
| `llm_base_url` | string/null | profile value | API-compatible provider 的 base URL。 |
| `llm_api_key` | string/null | empty | 可选凭据；profile API 不会明文返回。 |
| `evaluator_mode` | string/null | profile value | `mock`、`llm` 或 `hybrid`。 |
| `comfyui_base_url` | string/null | profile value | ComfyUI-backed run 的视频服务地址。 |
| `comfyui_workflows_dir` | string/null | profile value | 本地 workflow 搜索目录。 |
| `comfyui_workflow_id` | string/null | profile value | 选择的 workflow id。 |
| `comfyui_width` | integer/null | profile value | 范围：64-2048。 |
| `comfyui_height` | integer/null | profile value | 范围：64-2048。 |
| `comfyui_length` | integer/null | profile value | 范围：1-512。 |
| `comfyui_fps` | number/null | profile value | 范围：1-60。 |
| `comfyui_max_shots` | integer/null | profile value | 范围：0-32；`0` 表示不显式限制。 |
| `observer_provider_id` | string/null | profile value | 视觉观察 provider id。 |
| `vlm_model` | string/null | profile value | 视觉模型名。 |
| `vlm_base_url` | string/null | profile value | 本地或 API-compatible VLM base URL。 |
| `vlm_api_key` | string/null | empty | 可选凭据；profile API 不会明文返回。 |
| `vlm_frame_sample_count` | integer/null | `4` | 范围：1-16。 |
| `vlm_confidence_threshold` | number/null | `0.65` | 范围：0-1。 |
| `vlm_require_json` | boolean/null | `true` | 支持时要求 VLM 返回 JSON。 |

### Run 响应

`POST /api/runs` 返回：

| 字段 | 含义 |
| --- | --- |
| `project_id` | 用于版本快照的项目 id。 |
| `run_id` | 本地 run 目录 id。 |
| `version` | 当前版本。 |
| `exports` | export format 到本地文件路径的映射。 |
| `state` | 完整 `ProjectState`。 |

## Run 查询

### `GET /api/runs?limit=20`

返回最近 run 列表，包括 run id、idea、mode、provider profile、最新分数、版本和更新时间。

### `GET /api/runs/dashboard?limit=40`

返回工作台聚合状态：

- run 总数
- ready / needs revision / blocked 数量
- 平均 readiness score
- 每个 run 的生命周期、分数、问题数、artifact、export 和 blocker

### `GET /api/runs/{run_id}`

返回完整 `ProjectState`。

### `GET /api/runs/{run_id}/package-view`

返回分组后的 package view：

- `design`
- `generation`
- `observation`
- `evaluation`
- `iteration`
- `runtime`

当完整 state 对 UI 来说太扁平时，用这个接口更合适。

### `GET /api/runs/{run_id}/status`

返回 job 状态和进度步骤。缺失 run 返回 `404`。

### `GET /api/runs/{run_id}/trace`

返回 run package 中的 trace log。

### `GET /api/runs/{run_id}/harness`

返回运行时证据，包括 context snapshot、tool call、state transition、
workflow decision、policy record 和拓扑信息。

### `GET /api/runs/{run_id}/workbench`

返回产品工作台视角的数据：

- summary
- lifecycle steps
- overview metrics
- iteration timeline
- handoff center
- runtime evidence summary
- next actions

### `GET /api/runs/{run_id}/generation-artifacts`

返回生成产物元数据。每项包括 provider、version、iteration、shot id、本地路径、
以及 video、prompt text、prompt JSON、workflow payload 的下载 URL。

### `GET /api/runs/{run_id}/artifacts/{artifact_kind}/{iteration}/{shot_id}`

下载单个生成产物。

允许的 `artifact_kind`：

- `video`
- `prompt`
- `prompt_json`
- `workflow`

示例：

```text
GET /api/runs/20260609_1420/artifacts/video/v001/shot_01
```

### `GET /api/runs/{run_id}/readiness`

返回交付就绪状态、检查项、统计、交付物、下一步动作和风险。如果没有 readiness report，
返回 `404`。

### `GET /api/runs/{run_id}/versions`

返回该 project id 下保存的版本快照。

## 导出

### `GET /api/runs/{run_id}/export/{export_format}`

下载导出文件。支持：

| Format | File |
| --- | --- |
| `json` | `package.json` |
| `package_view` | `package_view.json` |
| `csv` | `package.csv` |
| `markdown` 或 `md` | `package.md` |
| `manifest` | `manifest.json` |
| `trace` | `trace.json` |
| `run_summary` 或 `summary` | `run_summary.md` |
| `evaluation_csv` 或 `evaluation` | `evaluation.csv` |

不支持的 format 返回 `400`，文件缺失返回 `404`。

## Provider APIs

### `GET /api/provider-profiles`

返回保存的 provider profiles、默认 profile 和 profile 存储路径。API key 会被脱敏，
只返回 `has_llm_api_key` 和 `has_vlm_api_key`。

### `POST /api/provider-profiles`

创建或更新 provider profile。

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
  "comfyui_fps": 8,
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

### `POST /api/preflight`

对一个 provider profile 形状的 payload 执行预检。响应字段：

| 字段 | 含义 |
| --- | --- |
| `status` | `passed`、`warning` 或 `failed`。 |
| `failed` | failed 检查数。 |
| `warnings` | warning 检查数。 |
| `checks` | `{check_id, label, status, detail}` 列表。 |
| `profile` | 脱敏后的 profile payload。 |

### `GET /api/observer-providers`

返回视觉观察 provider 描述和默认 profile。

### `GET /api/comfyui/workflows?root=<path>`

从配置的 workflow roots 和可选 `root` 参数中发现 API-format workflow。响应包含：

- `enabled`
- `base_url`
- `workflow_id`
- `workflows_dir`
- `workflows`
- `warnings`

### `POST /api/test-chain`

运行内置本地测试链路，用于安装可用性检查，不替代真实 provider preflight。

## CLI 参考

| Command | 用途 |
| --- | --- |
| `shotforge design "idea"` | 生成 storyboard、prompt package 和导出文件。 |
| `shotforge full-loop "idea"` | 运行设计、生成、评估、readiness 和导出。 |
| `shotforge full-loop "idea" --redesign --max-iterations 3` | 在评估后追加迭代 redesign。 |
| `shotforge evaluate data/runs/{run_id}/package.json` | 评估已有 package。 |
| `shotforge inspect data/runs/{run_id}/package.json` | 打印 package 摘要。 |
| `shotforge audit data/runs/{run_id}/package.json` | 打印运行时证据。 |
| `shotforge capabilities` | 打印 provider、agent、route 和 export 能力。 |
| `shotforge comfyui-workflows --root <path>` | 列出 workflow 文件和 callability。 |
| `shotforge doctor --deep` | 检查存储和 provider readiness。 |
| `shotforge web --reload` | 启动本地 Web 应用。 |
