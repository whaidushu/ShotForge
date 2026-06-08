# 产品线

产品线是 ShotForge 面向用户的一层。它把底层 runtime 做成短视频工作台，让用户可以配置 provider、运行生成闭环、查看 prompt 变化和视频产物，并导出交付包。

## 当前产品表面

当前 Web 应用分成两页：

- **Workflow page**：创意输入、模式选择、运行进度、storyboard、prompt changes、生成视频、评估报告、修正计划、版本链和导出。
- **Configuration page**：provider profiles、LLM/Judge 设置、视频 provider 设置、ComfyUI workflow 搜索、视觉观察器设置、preflight 和本地 readiness 测试。

产品表面应优先使用 provider profile。普通用户不应该每次 API 调用都手动传本地服务 URL。

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
