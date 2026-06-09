# 开发

## 环境

```powershell
conda activate ShotForge
pip install -e ".[dev]"
```

## 检查

```powershell
ruff check src tests
pytest -q
```

开发时可以跑聚焦测试：

```powershell
pytest tests/test_web.py tests/test_cli.py -q
```

## 项目结构

```text
src/shotforge/
  app/                 CLI、Web app、共享应用服务
  agents/              workflow agents
  core/                state、context、trace、versioning
  evaluators/          evaluation contract 和实现
  generators/          视频生成 provider
  observation/         抽帧和视觉观察
  workflows/           LangGraph workflow 定义
```

## 添加 Provider

1. 在对应 package 下添加 provider 实现。
2. 在 provider catalog 或 runtime service 中注册。
3. 如果需要用户配置，补充 profile 字段。
4. 为缺失服务、模型、路径或凭据添加 preflight 检查。
5. 用聚焦测试覆盖 provider contract。

## 文档范围

公开文档应保持用户导向。内部规划、面试材料、路线草稿和设计探索放在 `_private/`，
该目录已被 git ignore。
