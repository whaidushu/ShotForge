# UI 工程框架

Web UI 需要支撑后续持续打磨，因此样式、交互和资源应集中管理，而不是散在模板里。

## 目录模型

```text
src/shotforge/app/web/static/
  design-system.css
  shotforge-ui.js
  README.md

src/shotforge/templates/
  index.html
  partials/
```

## 设计系统规则

- 通用颜色、间距、阴影、按钮、表单和布局变量放在 `design-system.css`。
- 浏览器行为放在 `shotforge-ui.js`。
- 复杂页面拆成 partials。
- 不在模板里继续堆大量内联脚本和样式。

## 当前页面

- Workflow page：创意输入、运行进度、storyboard、prompt changes、视频产物、评估、版本和导出。
- Configuration page：provider profiles、LLM/Judge、视频 provider、ComfyUI workflow discovery、preflight、readiness testing。

## 工程边界

UI 不应该了解底层 provider 细节。它只应该通过 API 和 service 层读取：

- provider profiles
- observer providers
- preflight results
- run status
- workbench data
- generation artifacts

## 下一步

- 强化侧边栏和 run workspace。
- 保持配置页与工作流页分离。
- 统一图标、按钮、表格、卡片和空状态。
- 让 prompt changes 和 video artifacts 成为工作台核心，而不是附属信息。
