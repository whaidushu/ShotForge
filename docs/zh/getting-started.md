# 快速开始

这份文档用于把 ShotForge 在本地跑起来。

## 安装

```powershell
git clone https://github.com/whaidushu/ShotForge.git
cd ShotForge
conda create -n ShotForge python=3.11 pip -y
conda activate ShotForge
pip install -r requirements.txt
pip install -e .
```

开发环境可以额外安装：

```powershell
pip install -e ".[dev]"
```

## 运行检查

```powershell
ruff check src tests
pytest -q
```

## 启动 Web 应用

```powershell
shotforge web --reload
```

打开：

```text
http://127.0.0.1:8000
```

如果还没有配置本地模型服务，可以先看 demo：

```text
http://127.0.0.1:8000/demo?language=zh
```

## 运行 CLI

```powershell
shotforge design "一只赛博猫在雨夜上海屋顶追逐发光无人机" --language zh
shotforge full-loop "日出时穿越沙漠的霓虹列车" --language zh
```

## 输出目录

运行产物默认写入：

```text
data/runs/{run_id}
```

每次 run 可以包含提示词、workflow payload、生成视频、抽帧结果、视觉观察、
评估报告、版本 diff、trace 和导出文件。

## 下一步

- 在 [配置](configuration.md) 中配置真实 provider。
- 在 [Provider](providers.md) 中查看支持的 provider 类型。
- 在 [评估](evaluation.md) 中理解评估闭环。
