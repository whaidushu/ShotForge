# 项目主线与演示路径

## 一句话

ShotForge 是一个本地优先的 AI 视频工作台，把 provider 配置、生成、视觉观察、分层评估、修正、版本管理和导出串成一条可检查的运行链路。

## 主线

```text
用户创意
-> Provider Profile
-> ProjectState
-> 设计包
-> Prompt / Template Package
-> 视频产物
-> 帧抽取与视觉观察
-> 分层评估
-> 修正计划
-> 再生成
-> 版本 Diff 与运行历史
-> 导出文件
```

核心对象是 run，而不是单条 prompt。Run 包含创意目标、provider profile、prompt package、视频/帧/导出产物、物理目标、评估报告、修正计划、版本快照和运行时审计。

## 当前运行时模块

- `ProjectState`：跨 agents、providers、evaluation、exports、versioning 的类型化状态。
- `RunService`：Web/API 运行创建和导出编排。
- `ProviderService` / `ProviderRuntimeService`：provider 目录、profile、校验和运行时设置。
- `ComfyUIWorkflowService`：内置和本地 API-format workflow 搜索。
- `ArtifactService`：prompt、workflow、video、frame 产物查询。
- `VideoObservationService`：抽帧和观察器执行。
- `EvaluationAgent`：物理、连续性、静态和 LLM/Judge 评估信号。
- `VersionManager` / `VersionDiffBuilder`：快照、diff 和运行历史。
- `AgentHarnessRuntime`：上下文、工具、策略、沙箱、记忆和运行时审计。

## Web 演示路径

```powershell
shotforge web --reload
```

打开：

```text
http://127.0.0.1:8000
```

建议顺序：

1. 打开配置页，选择或保存 provider profile。
2. 运行 preflight，确认 provider readiness。
3. 回到 workflow 页输入创意。
4. 运行 design 或 full-loop。
5. 查看 storyboard、prompt package 和生成产物。
6. 查看 physical targets、observations、evaluation issues 和 correction plan。
7. 对比版本变化并导出 run package。

## CLI 验证路径

```powershell
shotforge design "A cyber cat chases a glowing drone across rainy Shanghai rooftops" --language en
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
shotforge audit data/runs/{run_id}/package.json
```

## API 检查路径

`GET /api/runs/{run_id}/workbench` 是产品级检查入口。

`GET /api/runs/{run_id}/harness` 是运行时级检查入口。

## 当前边界

ShotForge 目前仍是本地优先：已经具备 Web/CLI/API、provider profile、ComfyUI 接入、local test provider、分层评估、版本产物和 runtime audit。生产化部署、认证、多租户、持久存储、可观测性和配额控制需要独立规划。
