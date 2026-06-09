# 评估

ShotForge 把视频评估作为迭代闭环处理，而不是只给一个分数。

## 分层

评估从具体视觉事实开始，再逐步走向更主观的创意质量：

1. `physical_effect`：主体、物体数量、颜色、地点、天气、动作。
2. `frame_consistency`：物体、身份和动作是否在帧与帧之间保持稳定。
3. `style_color`：风格、色彩、光照和视觉处理。
4. `emotion_atmosphere`：情绪、张力和氛围。
5. `prompt_execution`：生成的提示词包是否遵循用户意图和修正计划。

## 观察

视频 run 可以抽帧、调用视觉观察 provider，并把 observation 附加到评估报告中。
这样评估器检查的是实际渲染产物，而不只是提示词文本。

## 迭代

当评估发现缺口时，correction 步骤可以把以下内容写回 prompt/template package：

- 必须可见的元素
- 缺失的物理目标
- 动作约束
- 负向约束
- 版本说明

下一次生成会保留前一次 run，用版本 diff 和 run history 支持对比。
