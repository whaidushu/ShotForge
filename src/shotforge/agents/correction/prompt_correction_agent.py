from __future__ import annotations

from shotforge.agents.correction._helpers import (
    effect_contracts_for_shot,
    localized_note,
    negative_constraints_for_issues,
    operation,
    physical_convergence_contracts,
    target_issues,
    target_shot_ids,
)
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState, runtime_language


class PromptCorrectionAgent(CorrectionAgent):
    correction_type = "prompt"
    agent_name = "prompt_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        issues = target_issues(state, plan)
        operations = []
        for shot_id in target_shot_ids(state, plan):
            shot_issues = [issue for issue in issues if issue.shot_id == shot_id]
            contracts = [
                *effect_contracts_for_shot(shot_issues, shot_id, runtime_language(state)),
                *physical_convergence_contracts(plan),
            ]
            addendum = " ".join([self._prompt_addendum(state, shot_id), *contracts]).strip()
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    addendum,
                    plan.correction_strategy,
                    metadata={"effect_contract": bool(contracts)},
                )
            )
            if contracts:
                operations.append(
                    operation(
                        "append_structured_template_list",
                        shot_id,
                        f"prompt_package.prompts[{shot_id}].structured_template.success_criteria",
                        contracts,
                        plan.correction_strategy,
                        metadata={"effect_contract": True},
                    )
                )
            negative = negative_constraints_for_issues(shot_issues)
            if negative:
                operations.append(
                    operation(
                        "append_negative_prompt",
                        shot_id,
                        f"prompt_package.prompts[{shot_id}].negative_prompt",
                        negative,
                        plan.correction_strategy,
                    )
                )
        return CorrectionPatch(
            plan_id=plan.plan_id,
            agent_name=self.agent_name,
            target_version=target_version,
            operations=operations,
            rationale=plan.correction_strategy,
            expected_effect=localized_note(runtime_language(state), "agents.correction.prompt.effect", plan, issues),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )

    def _prompt_addendum(self, state: ProjectState, shot_id: str) -> str:
        shot = next(item for item in state.shots if item.shot_id == shot_id)
        motion = shot.motion
        audio = next((item for item in state.audio_cues if item.shot_id == shot_id), None)
        if runtime_language(state) == "en":
            parts = [
                f"Keep the subject centered on {shot.title.lower()}",
                f"use {shot.shot_type}",
            ]
            if motion:
                parts.append(f"camera: {motion.camera}")
                parts.append(f"motion: {motion.subject_motion}")
            if audio:
                parts.append(f"sync visual emphasis to {audio.music}")
            parts.append("make timing, focal subject, and success beat visible on screen")
            return ". ".join(parts) + "."
        parts = [
            f"保持“{shot.title}”的主体清晰可见",
            f"使用{shot.shot_type}",
        ]
        if motion:
            parts.append(f"镜头运动为{motion.camera}")
            parts.append(f"主体动作表现为{motion.subject_motion}")
        if audio:
            parts.append(f"画面重点与“{audio.music}”的节奏对齐")
        parts.append("让时机、视觉焦点和关键完成点在画面中可直接观察")
        return "。".join(parts) + "。"
