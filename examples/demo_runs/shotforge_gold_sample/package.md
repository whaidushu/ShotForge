# ShotForge Production Package

Project: `proj_f24742c75474`
Run: `shotforge_gold_sample`
Version: `3`

## Idea

A quiet revenge reveal in a luxury elevator

## Intent

- Genre: cinematic
- Mood: energetic
- Visual Style: cinematic
- Audience: digital video viewers

## Storyboard

### Scene 1 - Hook

- Duration: 6s
- Shot: wide establishing
- Description: A woman in a dark tailored suit enters a mirrored luxury elevator, rain dripping from the tip of her umbrella. She hides a black access card in her palm as the former partner who betrayed her slips in before the doors close.
- Key visuals: cinematic, mirrored elevator, black access card, rain on umbrella tip, former partner, clear focal subject, layered environment detail

- Camera: low wide shot reflected in elevator mirrors
- Motion: she steps in, hides the access card, and never looks directly at him
- Transition: doors close into a hard cut
- Music: low pulse under elevator hum
- Sound design: rain drip on marble, soft elevator chime, doors sealing shut
- Prompt: PHYSICAL TARGETS: keep all explicitly requested visible elements on screen. MANDATORY VISIBLE ELEMENTS: . A woman in a dark tailored suit enters a mirrored luxury elevator, rain dripping from the tip of her umbrella. She hides a black access card in her palm as the former partner who betrayed her slips in before the doors close.. wide establishing, low wide shot reflected in elevator mirrors, she steps in, hides the access card, and never looks directly at him. Visual style: cinematic. Key visuals: cinematic, mirrored elevator, black access card, rain on umbrella tip, former partner, clear focal subject, layered environment detail. Audio intent: low pulse under elevator hum.

### Scene 2 - Escalation

- Duration: 6s
- Shot: tracking medium
- Description: She lightly taps the black access card against a hidden scanner. The floor display jumps from 12 to private floor 88. As he looks down, the mirrored metal tag on her briefcase reveals the logo of the prototype he stole. Make the card tap, floor jump, and briefcase reveal happen as three separate visible actions.
- Key visuals: cinematic, hidden scanner, floor 12 to 88, prototype logo, metal briefcase, clear focal subject, layered environment detail

- Camera: tight tracking shot from access card to floor indicator to reflected briefcase logo
- Motion: she taps the scanner, lets the floor number jump, and tilts the briefcase into his sightline Make the card tap, floor jump, and briefcase reveal happen as three separate visible actions. EFFECT CONTRACT: ACTION READABILITY - use one clear verb, one target object, and one visible reaction/outcome; avoid abstract motion language. EFFECT CONTRACT: make the target issue visibly measurable in the generated frames. Target dimension: pacing_progression.
- Transition: floor display flash cut
- Music: pulse tightens with a metallic tick
- Sound design: scanner beep, floor indicator jump, briefcase latch click
- Prompt: PHYSICAL TARGETS: keep all explicitly requested visible elements on screen. MANDATORY VISIBLE ELEMENTS: . She lightly taps the black access card against a hidden scanner. The floor display jumps from 12 to private floor 88. As he looks down, the mirrored metal tag on her briefcase reveals the logo of the prototype he stole.. tracking medium, tight tracking shot from access card to floor indicator to reflected briefcase logo, she taps the scanner, lets the floor number jump, and tilts the briefcase into his sightline. Visual style: cinematic. Key visuals: cinematic, hidden scanner, floor 12 to 88, prototype logo, metal briefcase, clear focal subject, layered environment detail. Audio intent: pulse tightens with a metallic tick. Revision target for shot_02: Make the card tap, floor jump, and briefcase reveal happen as three separate visible actions. Keep these visible anchors measurable on screen: cinematic, hidden scanner, floor 12 to 88, prototype logo, metal briefcase, clear focal subject. EFFECT CONTRACT: ACTION READABILITY - use one clear verb, one target object, and one visible reaction/outcome; avoid abstract motion language. EFFECT CONTRACT: make the target issue visibly measurable in the generated frames. Target dimension: pacing_progression. Use: start pose -> continuous movement -> end pose. Revision target for shot_02: Make the card tap, floor jump, and briefcase reveal happen as three separate visible actions. Keep these visible anchors measurable on screen: cinematic, hidden scanner, floor 12 to 88, prototype logo, metal briefcase, clear focal subject. EFFECT CONTRACT: ACTION READABILITY - use one clear verb, one target object, and one visible reaction/outcome; avoid abstract motion language. Use: start pose -> continuous movement -> end pose.

### Scene 3 - Signature Moment

- Duration: 6s
- Shot: dynamic close-up
- Description: The elevator lights blink off and return. A wall screen plays security footage of him handing the company's encryption key to a competitor. She finally raises her eyes, with her face and the evidence screen layered in the mirror.
- Key visuals: cinematic, security footage, company encryption key, competitor, mirror overlay, clear focal subject, layered environment detail

- Camera: slow orbit close-up that keeps her eyes, his reflection, and the evidence screen aligned
- Motion: she raises her eyes as the evidence screen lights up and he freezes mid-breath
- Transition: blackout blink into evidence screen
- Music: sub-bass drop under a thin glass tone
- Sound design: lights flicker, screen turns on, his breath stops
- Prompt: PHYSICAL TARGETS: keep all explicitly requested visible elements on screen. MANDATORY VISIBLE ELEMENTS: . The elevator lights blink off and return. A wall screen plays security footage of him handing the company's encryption key to a competitor. She finally raises her eyes, with her face and the evidence screen layered in the mirror.. dynamic close-up, slow orbit close-up that keeps her eyes, his reflection, and the evidence screen aligned, she raises her eyes as the evidence screen lights up and he freezes mid-breath. Visual style: cinematic. Key visuals: cinematic, security footage, company encryption key, competitor, mirror overlay, clear focal subject, layered environment detail. Audio intent: sub-bass drop under a thin glass tone.

### Scene 4 - Resolution

- Duration: 6s
- Shot: hero wide
- Description: The elevator opens onto an empty boardroom on floor 88, every seat lit by the same evidence file. She walks out and drops the access card on the marble. As the doors close, he remains trapped inside and the floor counter begins to count down.
- Key visuals: cinematic, floor 88 boardroom, evidence files, dropped access card, countdown display, clear focal subject, layered environment detail

- Camera: wide pullback from opening doors to the empty boardroom table
- Motion: she exits without turning back, drops the card, and leaves him trapped in the closing reflection
- Transition: doors close on his reflection
- Music: low pulse resolves into a cold sustained note
- Sound design: doors opening, card hitting marble, floor counter ticking down
- Prompt: PHYSICAL TARGETS: keep all explicitly requested visible elements on screen. MANDATORY VISIBLE ELEMENTS: . The elevator opens onto an empty boardroom on floor 88, every seat lit by the same evidence file. She walks out and drops the access card on the marble. As the doors close, he remains trapped inside and the floor counter begins to count down.. hero wide, wide pullback from opening doors to the empty boardroom table, she exits without turning back, drops the card, and leaves him trapped in the closing reflection. Visual style: cinematic. Key visuals: cinematic, floor 88 boardroom, evidence files, dropped access card, countdown display, clear focal subject, layered environment detail. Audio intent: low pulse resolves into a cold sustained note.


## Solution Architecture

- Industry: Media and Entertainment
- Scenario: AI video production planning
- Business objective: Reduce creative planning latency and make video prompt production auditable.
- Model strategy: Mock LLM in POC, pluggable video providers for ComfyUI/Jimeng/Kling/Runway/Open-Sora.
- Knowledge assets: media_advertising_video_ops, evaluation_rubrics.json, prompt_rules.json, correction_strategies.json
- Scenario patterns: campaign concept to storyboard package, brand-safe short-video production planning, multi-provider video model comparison
- Evaluation metrics: story clarity, brand fit, motion readability, prompt executability

### Agent components

- ProjectState / AgentHarnessRuntime: Single structured state across creative, runtime, evaluation, and exports.
- ContextBuilder / all_agents: Build scoped context packets for each agent from state, knowledge, and memory.
- SkillRegistry / AgentHarnessRuntime: Register local tools and record tool-call purpose, status, latency, and permission scope.
- MCP / Sandbox / Memory / AgentHarnessRuntime: Expose local resources, constrained execution, and reusable run memory as extension points.

### POC success criteria

- creative package turnaround: < 2 minutes for mock pipeline (trace log timestamps and export completion)
- agent harness observability: context, tool calls, policies, MCP, sandbox, and memory visible per run (Harness Inspector and exported ProjectState)
- closed-loop improvement readiness: evaluation, correction plan, diff, and verification generated (planning mode output)
- story clarity: measurable in evaluation report (scenario playbook rubric mapping)
- brand fit: measurable in evaluation report (scenario playbook rubric mapping)
- motion readability: measurable in evaluation report (scenario playbook rubric mapping)

### Rollout plan

- POC: validate workflow, schema, exports, and demo narrative
- Pilot: connect one real provider and one customer asset source
- Production: add tenancy, governance, monitoring, and cost controls

### Value metrics

- Speed: shorter campaign iteration cycle (manual creative brief and storyboard drafting -> structured task package generated in one run)
- Stability: repeatable delivery and easier issue diagnosis (untracked prompt experiments -> state, versions, trace, and tool calls retained)
- Cost control: reduce wasted generation calls (trial-and-error external generation -> pre-flight evaluation before real model spend)
- speed: connect solution design to customer KPI (not tracked before POC -> tracked as a scenario value lever)
- creative consistency: connect solution design to customer KPI (not tracked before POC -> tracked as a scenario value lever)


## Delivery Readiness

- Overall status: warning

### Readiness checks

- [passed] State Management / state_schema: 4 shots, 4 prompts, version v1 Remediation: Generate intent, storyboard, motion, audio, and prompt package before handoff.- [passed] Context Engineering / context_observability: 7 context snapshots recorded Remediation: Enable AgentHarnessRuntime context snapshots for every agent.- [warning] Tool Orchestration / tool_policy: 2 tool calls, scopes=['local_inference'] Remediation: Record permission scope and execution status for all production tools.- [passed] Tool Orchestration / tool_orchestration: 2 tool plans, failed=0, fallback_used=0 Remediation: Review denied tools, schema failures, and fallback outcomes before pilot.- [passed] State Management / state_transition_audit: 6 transitions, issues=0 Remediation: Review state transition warnings before pilot handoff.- [passed] Agent Harness / agent_contracts: 6 contract reports, failed=0 Remediation: Review failed agent contracts before pilot handoff.- [passed] Workflow Routing / workflow_decisions: 6 routing decisions, critical=0, gate_snapshots=6 Remediation: Resolve critical workflow routing decisions before export.- [passed] Context Engineering / context_safety: 7 context digests, redacted_sources=0 Remediation: Ensure every agent context has digest and redaction metadata.- [passed] MCP / mcp_capability: mcp_tools=['knowledge.search', 'runs.get_harness_audit', 'runs.get_package', 'runs.list'], missing=[], access_records=14, denied=0 Remediation: Expose required MCP tools before external tool-host integration.- [passed] Memory / memory_strategy: memory_refs=3, selection_records=13, promotion_decisions=0 Remediation: Promote successful runs or seed customer memory before pilot.- [passed] Sandbox / sandbox_strategy: 7 sandbox records, denied=0, boundary_snapshots=7 Remediation: Review denied sandbox activity and enforce workspace boundary before pilot.- [passed] Solution Design / solution_architecture: 4 components, 7 integrations Remediation: Generate customer-facing solution architecture before delivery.- [passed] Delivery Package / export_contract: available=['export.csv', 'export.json', 'export.manifest', 'export.markdown', 'export.run_summary', 'export.trace'], missing=[] Remediation: Register all required export skills.- [warning] Model Strategy / provider_strategy: prompt provider=mock-video-model Remediation: Configure one real video provider and credentials for pilot.- [warning] Effect Evaluation / evaluation_loop: evaluations=0, redesign_plans=0, verification_reports=0 Remediation: Run full_loop or planning mode to produce evaluation and correction evidence.
### Handoff deliverables

- ProjectState JSON package
- Storyboard CSV package
- Markdown production brief
- Harness evidence trace
- Solution architecture summary
- Delivery readiness report

### Next actions

- Record permission scope and execution status for all production tools.
- Configure one real video provider and credentials for pilot.
- Run full_loop or planning mode to produce evaluation and correction evidence.
- Select one pilot customer scenario and bind success criteria to measurable data.


## Mock Generation

- Provider: mock
- Status: mocked
- Result: `gen_b23051294916`

- shot_01: shot_01 mocked a 'Hook' beat with possible weak action, emotion, or audio timing.
- shot_02: shot_02 mocked a 'Escalation' beat with possible weak action, emotion, or audio timing.
- shot_03: shot_03 mocked a 'Signature Moment' beat with possible weak action, emotion, or audio timing.
- shot_04: shot_04 mocked a 'Resolution' beat with possible weak action, emotion, or audio timing.

## Evaluation Report

- Evaluation: `eval_3ae2c3527055`
- Rubric: baseline_v1
- Overall score: 0.85

### Dimension Scores

- Subject Count (`subject_count`): 0.95 - Subject Count is computed from 4 evaluator signals.
- Element Presence (`element_presence`): 0.88 - Element Presence is computed from 4 evaluator signals.
- Element Description (`element_description`): 1.00 - Element Description is computed from 4 evaluator signals.
- Character Consistency (`character_consistency`): 0.82 - Character Consistency is computed from 4 evaluator signals.
- Frame Element Consistency (`frame_element_consistency`): 1.00 - Frame Element Consistency is computed from 4 evaluator signals.
- Frame Action Consistency (`frame_action_consistency`): 1.00 - Frame Action Consistency is computed from 4 evaluator signals.
- Face Identity Consistency (`face_identity_consistency`): 1.00 - Face Identity Consistency is computed from 4 evaluator signals.
- Scene Consistency (`scene_consistency`): 0.80 - Scene Consistency is computed from 4 evaluator signals.
- Action Clarity (`action_clarity`): 0.77 - Action Clarity is computed from 4 evaluator signals.
- Pacing Progression (`pacing_progression`): 0.73 - Pacing Progression is computed from 4 evaluator signals.
- Color Alignment (`color_alignment`): 0.88 - Color Alignment is computed from 4 evaluator signals.
- Camera Expression (`camera_expression`): 0.75 - Camera Expression is computed from 4 evaluator signals.
- Emotional Intensity (`emotional_intensity`): 0.71 - Emotional Intensity is computed from 4 evaluator signals.
- Reversal Expression (`reversal_expression`): 0.61 - Reversal Expression is computed from 4 evaluator signals.
- Audio Timing (`audio_timing`): 0.71 - Audio Timing is computed from 4 evaluator signals.
- Prompt Executability (`prompt_executability`): 0.86 - Prompt Executability is computed from 8 evaluator signals.

### Issues

- [low] shot_02 / Action Clarity / action: The main action target in shot_02 is not explicit enough. Cause: Action verbs, target objects, or reaction outcomes are not concrete enough.
- [low] shot_01 / Color Alignment / scene: shot_01 underperforms on Color Alignment. Cause: Color, material, or glow attributes are not written as hard constraints.
- [low] shot_02 / Color Alignment / scene: shot_02 underperforms on Color Alignment. Cause: Color, material, or glow attributes are not written as hard constraints.
- [medium] shot_04 / Camera Expression / camera: Camera language in shot_04 does not support the narrative beat strongly enough. Cause: Shot type, camera motion, or subject relationship is under-specified.
- [medium] shot_03 / Emotional Intensity / emotion: The emotional expression in shot_03 is not strong enough. Cause: Emotional action, facial detail, or audio turn design is insufficient.
- [high] shot_03 / Reversal Expression / scene: The reversal or key information anchor in shot_03 is not explicit enough. Cause: Visual anchors, before/after contrast, or reveal actions are missing.
- [medium] shot_04 / Audio Timing / audio: Audio timing in shot_04 is not aligned with the visual beat. Cause: Sound trigger, BGM transition, or ambience layering is under-specified.

### Suggested Focus

- frame_consistency:action:Action Clarity
- style_color:scene:Color Alignment
- style_color:camera:Camera Expression
- emotion_atmosphere:emotion:Emotional Intensity
- emotion_atmosphere:scene:Reversal Expression

## Trace

- 2026-06-03 09:27:40.116274+00:00 - verification_agent - started- 2026-06-03 09:27:40.116327+00:00 - verification_agent - completed - 0.05ms- 2026-06-03 09:27:40.116346+00:00 - evaluation_agent - started- 2026-06-03 09:27:40.129517+00:00 - evaluation_agent - completed - 13.17ms