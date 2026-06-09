# 开发

这份文档说明本地开发、测试和扩展模式。

## 环境

```powershell
conda activate ShotForge
pip install -e ".[dev]"
```

## 检查

运行标准检查：

```powershell
ruff check src tests
pytest -q
```

开发时可以运行聚焦测试：

```powershell
pytest tests/test_web.py tests/test_cli.py -q
```

## 项目结构

```text
src/shotforge/
  app/
    api/             FastAPI routers 和 API schemas
    cli/             Typer CLI commands
    services/        Web/API 共享应用服务
    web/             FastAPI pages、templates、static UI assets
  agents/            workflow agents
  core/              state、packages、trace、versioning、runtime evidence
  evaluators/        evaluation contracts 和实现
  exporters/         JSON、CSV、Markdown、manifest、trace exporters
  generators/        video generator provider contracts 和 adapters
  i18n/              英文和中文 UI/output strings
  knowledge/         rubric 和 prompt-support assets
  observation/       抽帧、frame observers、sequence observation
  workflows/         LangGraph workflow definitions
```

## 添加 API Endpoint

1. 如果 endpoint 接收结构化输入，在 `src/shotforge/app/api/schemas.py` 添加请求/响应模型。
2. 在 `src/shotforge/app/api/` 下对应 router 添加 route。
3. 将业务逻辑放在 `src/shotforge/app/services/`，不要堆在 route function 中。
4. 为成功和失败场景添加测试。
5. 更新 [API 参考](api-reference.md)。

## 添加 Generator Provider

1. 实现 `GeneratorProvider` protocol。
2. 返回带有本地 artifact metadata 的 `GeneratedResult`。
3. 在 generator catalog 中注册 provider。
4. 如果 provider 需要配置，增加 provider profile 字段。
5. 增加 preflight 检查。
6. 为 `supports_real_generation`、`capabilities` 和失败模式添加测试。

## 添加 Visual Observer

1. 在 `observation/providers/registry.py` 添加 descriptor。
2. 实现 frame observer 或 VLM 调用 wrapper。
3. 返回包含 detected elements 和 summaries 的结构化 observation。
4. 只有 provider 需要 model/base URL/key 时才增加配置字段。
5. 增加 preflight 检查和测试。

## 添加 Evaluator

1. 实现 `EvaluatorProvider`。
2. 返回带分数和 evidence 的 `EvaluationSignal`。
3. 在 `EvaluatorRegistry.defaults()` 中注册。
4. 需要时增加 rubric dimensions 或 signal keys。
5. 为 issue 创建和 score 行为添加测试。

## 使用 State

如果数据是 run contract 的一部分，优先添加到 `ProjectState` 或 package models。
provider-specific 或临时细节可以放在 `metadata`。

会改变 state 的代码应当：

- 更新 `ProjectState`
- 需要时调用 `state.touch()`
- 对关键步骤增加 trace 或 runtime record
- workflow 完成后导出更新后的 package

## UI Assets

静态 UI 资产位于 `src/shotforge/app/web/static/`：

- `design-system.css`：tokens 和共享 layout primitives
- `shotforge-ui.js`：可复用浏览器行为
- `README.md`：static asset 组织说明

视觉组件保持可复用，provider/workflow 逻辑放在 service 中。

## 文档范围

公开文档应说明如何安装、配置、使用、检查和扩展项目。行为、endpoint 或配置字段变化时，
对应文档也应同步更新。
