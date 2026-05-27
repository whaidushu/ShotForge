# ShotForge / 镜铸 — 路线图与执行计划

> 生成日期：2026-05-23 | 从今天开始的两周推进计划
>
> 本文件是 ShotForge 项目本身的规划，不涉及字节面试准备（面试计划已在另一份 xlsx 中）。

---

##  核心思路



### 起源

当前文生视频领域所有人都在卷"一次生成质量"。但复杂组合性视频（多对象、属性绑定、动态交互、空间关系）本质上是 **系统工程问题**，不是模型能力问题。

参考 [GenMAC (CVPR 2025)](https://arxiv.org/abs/2412.04440) 的思路，ShotForge 将视频生成从 **"一次抽卡"** 变为 **"迭代收敛"**：

```
不是:  Prompt ────────────────→ 🎥 视频 (碰运气)

而是:  Prompt → 🧠 设计 → 🎥 生成 → 🔍 评估 → 🔧 修正 → 🔄 再生成 → ... → ✅ 收敛
```

### 三层核心叙事

| 层级 | 叙事 | 核心指标 |
|------|------|---------|
| **省钱** | 小模型迭代收敛（便宜），大模型精准生成（只花一次钱） | 大模型调用从 5-20 次降到 1 次 |
| **省心** | 把创作者模糊的"不满意"变成结构化可修正的问题 | 9维评估自动诊断 + 定向修正 |
| **省GPU** | 本地/小模型做迭代，商业API只做最终交付 | 迭代成本趋近于零 |

### 🛡️ 护城河

```
Layer 1: 代码层 (MIT 开源)        → 无壁垒，认了
Layer 2: 评估量表 (CC BY-NC-SA)   → 9维通用版开源，行业定制版闭源
Layer 3: 收敛配方 (企业版闭源)    → "游戏预告片怎么调pacing"是经验不是代码
Layer 4: 数据飞轮 (云服务聚合)     → 匿名使用模式反哺评估精确度
Layer 5: 模型适配持续性           → API一变更你就得追，但付费用户不用操心
```

---

## 🗺️ 版本路线图

| 阶段 | 核心价值 | 状态 |
|------|---------|------|
| **V0** | 创意→方案包（5 Agent Pipeline） | ✅ |
| **V1** | 9维评估 + Mock生成 | ✅ |
| **V2** | GeneratorProvider协议 + Redesign & Convergence Loop | ✅ 核心闭环完成 |
| **V3** | MP4导出 + ComfyUI真实生成接入 | 📋 |
| **V4** | GeneratorProvider体系 + 多模型路由 + 成本落地 | 📋 |
| **V5** | Agent Infra完整化 (MCP/Sandbox/Memory/RAG/HITL) | 📋 |
| **V6** | 社区Release + 插件市场 + Cloud | 📋 |

<details>
<summary><b>V0 · Design Harness · ✅</b></summary>

创意 → Intent → Storyboard → Motion → AudioCue → PromptAdapter → Export
产出：ProjectState, SceneSpec, ShotSpec, MotionSpec, AudioCue, PromptPackage
</details>

<details>
<summary><b>V1 · Evaluation Baseline · ✅</b></summary>

评估体系：9维评估 + SignalAggregator + EvaluatorProvider 可插拔协议
产出：ScoreCard, IssueList, EvaluationReport
</details>

<details>
<summary><b>V2 · GeneratorProvider + Redesign & Convergence · ✅ 核心闭环完成</b></summary>

**已完成：**
- GeneratorProvider 协议定义 + Mock 实现 + Provider Catalog
- Provider 下拉选择：Mock 可运行，ComfyUI / Open-Sora / Kling / Jimeng / Runway 已作为 planned provider 进入目录
- Redesign Loop：Verification → Suggestion → Correction(7个) → OutputStructuring
- CorrectionRouter：负责 plan → agent 路由，并记录 skip reason
- ConvergenceEngine：判断停止/继续/回归，支持用户配置 2-10 轮上限，默认 3 轮；生产包 unchanged 时提前截断
- 每轮迭代持久化 Version Snapshot，并通过 `/api/runs/{run_id}/versions` 暴露快照列表
- VersionDiff + ScoreDelta + RegressionCheck + ConvergenceStep
- Web 版本链路视图：按 V1→V2→V3 展示每轮 diff，默认展开最新一轮
- Correction 策略文案迁入 `knowledge/correction_strategies.json`，便于快速迭代

GenMAC 论文对应：Design=design_workflow, Generation=generators/base.py(协议),
Verification=verification_agent, Suggestion=suggestion_agent,
Correction=correction/*.py+router, OutputStruct=output_structuring_agent,
Iterative=convergence_engine

**待解决的核心问题（你提到了）：**
1. 评估器如何确定"创作者期望的方向"？（主观反馈→客观维度的映射）
2. 小模型评估的可靠性？（如果评估不准，修正方向就瞎了）
3. 修正不能引入回归（修A坏了B）→ RegressionCheck 要盯整体分数
</details>

<details>
<summary><b>V3 · MP4 Export + Local Generator · 📋</b></summary>

ComfyUI 本地生成 → FFmpeg拼接 → MP4(多画幅/多压缩比)
策略：只做基础拼接，不做剪辑器/BGM/字幕
超出边界 → DaVinci XML 对接专业工具
</details>

<details>
<summary><b>V4 · GeneratorProvider 体系 · 📋</b></summary>

全Provider接入：Mock → ComfyUI → Open-Sora → Kling/Runway/Jimeng
成本策略落地：迭代→本地零成本 | 交付→商业API只1次
</details>

<details>
<summary><b>V5 · Agent Infra · 📋</b></summary>

MCP/Sandbox/Memory/RAG/HITL/可观测性 — 让ShotForge成为Agent Harness标杆
</details>

<details>
<summary><b>V6 · 社区&生态 · 📋</b></summary>

插件市场 / 收敛配方 / Cloud(免费→$19-99→企业年费)
</details>

---

## 💰 开源+商业化三层阶梯

```
Layer 3: 企业版 (年费 $5k-30万)
  ┌────────────────────────────────────────────┐
  │ 私有部署 + 品牌风格库 + 行业评估维度         │
  │ 收敛配方(游戏/电商/广告场景的最佳迭代策略)     │
  │ SLA + 培训 + 专属支持                       │
  └────────────────────────────────────────────┘

Layer 2: ShotForge Cloud (月费 $19-99)
  ┌────────────────────────────────────────────┐
  │ 无需部署，网页直接用                         │
  │ 多模型API自动适配                           │
  │ 收敛配方持续更新                             │
  └────────────────────────────────────────────┘

Layer 1: 开源社区版 (永久免费)
  ┌────────────────────────────────────────────┐
  │ MIT 代码 + 基础9维评估量表                   │
  │ 获客引擎：让开发者先爱上你的产品               │
  │ 社区反馈反哺评估量表进化                      │
  └────────────────────────────────────────────┘
```

**商业化的本质：卖的不是代码，是"省心"。**

| 客户类型 | 为什么不自建 | 为什么付钱 |
|---------|-------------|----------|
| 独立创作者 | 不会部署 Python 环境 | 网页就能用 |
| 小团队 | 一台机器跑不动 | 云端并行 |
| 广告公司 | 需要品牌风格一致性 | 定制评估维度 |
| 视频制作公司 | 数据不能上公有云 | 私有化部署 |

---

## 🔌 License 分层策略

- **引擎代码** (`src/shotforge/` 下除 `knowledge/` 外)：**MIT** — 最大范围传播
- **知识资产** (`knowledge/` 目录)：**CC BY-NC-SA 4.0** — 开源可用，商用需授权

---

## 📅 ShotForge 两周推进计划

> 以 ShotForge 项目本身为第一优先级，不捆绑面试节奏。

### 第1周：V2开发冲刺

| 日 | 上午 | 下午 | 产出 |
|----|------|------|------|
| 5/26 一 | GeneratorProvider协议定义+Mock实现 | 重构workflows接入GeneratorProvider | ✅ `generators/base.py` + V2 workflow打通 |
| 5/27 二 | Redesign Loop: Verification→Suggestion打通 | Correction Router + 7个CorrectionAgent联调 | ✅ `redesign_workflow.py` 可运行 |
| 5/28 三 | OutputStructuringAgent + 重新生成链路 | ConvergenceEngine:得分收敛判断 | ✅ 多轮修正闭环跑通 |
| 5/29 四 | VersionDiff + RegressionCheck + Snapshot实现 | 端到端测试:Design→Eval→Redesign→ReEval | ✅ V2 完整闭环通过测试 |
| 5/30 五 | Badcase收集:用真实Prompts在Mock上跑 | 写V2总结+画架构对比图(ShotForge vs GenMAC) | V2 文档 + 架构图 |
| 5/31 六 | 🔄 Buffer日/补漏 | — | — |

### 第2周：V3 + 打磨

| 日 | 上午 | 下午 | 产出 |
|----|------|------|------|
| 6/1 日 | 学习ComfyUI API/本地部署 | 设计ComfyUIProvider对接方案 | ComfyUI调研笔记 |
| 6/2 一 | ComfyUIProvider实现+联通测试 | 真实生成→Evaluation→评分结果分析 | 首个真实生成评估数据 |
| 6/3 二 | FFmpeg MP4拼接+多画幅配置 | 端到端Demo:创意→方案包→MP4成品 | 第一个可见Demo |
| 6/4 三 | 评估量表校准:对比Mock vs 真实生成的评分差异 | 记录Badcase+修正策略效果 | 评估量表v2 |
| 6/5 四 | 中英README最终版 | draw.io架构图+技术博客大纲 | 可以开源的文档 |
| 6/6 五 | Demo视频录制(3分钟) | GitHub仓库最终准备+Release Notes | v0.2.0 Release! |
| 6/7+ | 🚀 发布 + 推广 | — | — |

---

## 📊 并发推进清单

以下模块与主线并行推进：

- [ ] 豆包LLM接入（MockLLM→真实LLM） — 验证Agent思路在真实模型上是否work
- [ ] 评估量表冷启动 — 用Kling API生成10个视频+人工打分，建Golden Dataset
- [ ] MCP协议定义 — `extensions/mcp.py` 升级为完整 `mcp/protocol.py`
- [ ] 竞品文档完善 — 你调研的10个竞品对比表整理到文档中
