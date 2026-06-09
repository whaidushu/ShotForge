# 产品线

产品线是 ShotForge 面向用户的一层。它把底层 runtime 做成短视频工作台，让用户可以配置 provider、运行生成闭环、查看 prompt 变化和视频产物，并导出交付包。

## 当前产品表面

当前 Web 应用分成两页：

- **Workflow page**：创意输入、模式选择、运行进度、storyboard、prompt changes、生成视频、评估报告、修正计划、版本链和导出。
- **Configuration page**：provider profiles、LLM/Judge 设置、视频 provider 设置、ComfyUI workflow 搜索、视觉观察器设置、preflight 和本地 readiness 测试。

产品表面应优先使用 provider profile。普通用户不应该每次 API 调用都手动传本地服务 URL。

## 产品完整度层

当前产品化工作不是完整重做 UI，而是先补一层面向审查者的完成度，让现有 runtime 能被当作工具理解：

- **先看内置样例**：公开审查者可以打开 `/demo?language=zh`，不配置 GPU 服务也能查看一个已完成任务。
- **Run 是产品对象**：工作台把每个视频任务组织成 run，包含生命周期、provider profile、产物、评估、版本、导出和审计证据。
- **配置和创作分离**：服务就绪检查放在 Configuration 页面，避免把创作流程和本地服务细节混在一起。
- **交付物可见**：导出文件、就绪门禁、trace 和任务包作为交付产物展示，而不是藏在实现细节里。

这是进一步打磨 UI 之前最小的一层产品完整度。它让审查者能在几分钟内理解工作流，同时仍然可以深入查看底层 Agent Harness 证据。

## 当前用户流程

```text
配置 provider profile
-> 运行 preflight
-> 输入创意
-> 生成设计包
-> 视频 provider 渲染产物
-> 抽帧并观察可见事实
-> 执行分层评估
-> 生成修正计划
-> 重新生成或导出
-> 对比版本和交付文件
```

## 产品需要显式展示

- 当前使用的 provider profile。
- LLM、视频、workflow、observer 是否 ready。
- 每轮 prompt 发生了什么变化。
- 每轮对应哪个视频产物。
- 哪些 physical targets 被要求、被观察到、缺失。
- 哪些评估问题驱动了修正计划。
- 哪些文件可以导出。

## 当前边界

当前范围：

- 单镜头 workflow，并为多镜头扩展保留结构。
- Provider profile 和本地 readiness 检查。
- ComfyUI workflow 搜索与 API-format workflow 执行。
- Prompt、workflow、video、frame、evaluation、export 产物。
- 版本历史和 prompt/evaluation diff。
- 从物理事实到抽象质量信号的分层评估。

暂不做：

- 完整时间线编辑器。
- 多人协作。
- 支付、配额和账号系统。
- 生产部署打包。
- 素材市场或完整媒体库。

## 下一步产品方向

- 强化 run workbench 布局和产物对比。
- 让 physical target extraction 和 missing-element correction 更可见。
- 增加多镜头数据结构，但不急着做复杂 UI。
- 保持配置页和创作流程分离。
- 降低部署复杂度，但不隐藏 provider readiness 要求。
