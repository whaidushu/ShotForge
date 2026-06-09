# 快速开始

这份文档用于在本地启动 ShotForge，并说明第一次 run 后应该检查什么。

## 安装

```powershell
git clone https://github.com/whaidushu/ShotForge.git
cd ShotForge
conda create -n ShotForge python=3.11 pip -y
conda activate ShotForge
pip install -r requirements.txt
pip install -e .
```

开发工具：

```powershell
pip install -e ".[dev]"
```

## 配置

创建本地环境文件：

```powershell
copy .env.example .env
```

没有真实模型服务时，也可以运行 demo 和 design-only workflow。完整视频生成需要配置 provider。
见 [配置](configuration.md) 和 [Provider](providers.md)。

## 运行检查

```powershell
ruff check src tests
pytest -q
```

检查 provider 和存储：

```powershell
shotforge doctor --deep
```

## 启动 Web 应用

```powershell
shotforge web --reload
```

打开：

```text
http://127.0.0.1:8000
```

模型服务还没配置时，可以先看 demo：

```text
http://127.0.0.1:8000/demo?language=zh
```

## 第一个 Web 流程

1. 打开 Configuration。
2. 创建或选择 provider profile。
3. 运行 preflight。
4. 回到 Workflow。
5. 输入 idea。
6. 运行 design 或 full-loop mode。
7. 检查 storyboard、prompt package、generated artifacts、evaluation issues、
   version changes 和 exports。

## CLI 示例

Design-only：

```powershell
shotforge design "日出时穿越沙漠的霓虹列车" --language zh
```

Full loop：

```powershell
shotforge full-loop "雨夜城市街道中的产品揭示镜头" --language zh --generator <provider-id>
```

带迭代 redesign：

```powershell
shotforge full-loop "雨夜城市街道中的产品揭示镜头" --language zh --redesign --max-iterations 3 --generator <provider-id>
```

检查已保存 package：

```powershell
shotforge inspect data/runs/{run_id}/package.json
shotforge audit data/runs/{run_id}/package.json
```

## 输出目录

Run 输出写入：

```text
data/runs/{run_id}
```

常见文件：

- `package.json`
- `package_view.json`
- `package.csv`
- `package.md`
- `manifest.json`
- `trace.json`
- `run_summary.md`
- `evaluation.csv`
- generated videos
- prompt text 和 prompt JSON
- workflow payloads
- extracted frames

## Run 后检查

- `GET /api/runs/{run_id}/workbench`：产品工作台状态。
- `GET /api/runs/{run_id}/generation-artifacts`：artifact links。
- `GET /api/runs/{run_id}/harness`：runtime evidence。
- `GET /api/runs/{run_id}/versions`：version snapshots。
- `data/runs/{run_id}/package.json`：完整保存状态。
