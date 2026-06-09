# ShotForge Run Summary

- Project: `proj_d41bd05dc0b0`
- Run: `shotforge_gold_sample_zh`
- Version: `3`
- Idea: 一场发生在豪华电梯里的安静复仇揭露
- Shots: 4
- Exports: 5

## Solution

- Industry: 影视内容
- Scenario: AI 视频生产策划
- Playbooks: media_advertising_video_ops, evaluation_rubrics.json, prompt_rules.json, correction_strategies.json
- Acceptance criteria: 6

## Delivery Readiness

- Overall status: warning
- Checks: 15
- Next actions: 4
  - 为所有生产工具记录权限范围和执行状态。
  - 为试点配置一个真实视频生成服务和凭证。
  - 运行 full_loop 或 planning 模式，生成评估与修正证据。
  - 选择一个试点客户场景，并将成功标准绑定到可度量数据。

## Harness Evidence

- Context snapshots: 8
- Tool calls: 10
- State transitions: 8
- Agent topology nodes: 8
- Agent topology edges: 7

## Audit

- Harness API: `/api/runs/shotforge_gold_sample_zh/harness`
- CLI: `shotforge audit examples\demo_runs\shotforge_gold_sample_zh\package.json`
