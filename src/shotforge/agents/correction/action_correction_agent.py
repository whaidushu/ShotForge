from __future__ import annotations

from shotforge.agents.correction._helpers import localized_note, operation, target_issues, target_shot_ids
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState


class ActionCorrectionAgent(CorrectionAgent):
    correction_type = "action"
    agent_name = "action_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        issues = target_issues(state, plan)
        note = localized_note(state.language, "agents.correction.action.note", plan, issues)
        operations = []
        for shot_id in target_shot_ids(state, plan):
            operations.append(
                operation(
                    "append_shot_description",
                    shot_id,
                    f"shots[{shot_id}].description",
                    note,
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_motion_subject",
                    shot_id,
                    f"shots[{shot_id}].motion.subject_motion",
                    localized_note(state.language, "agents.correction.action.motion", plan, issues),
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    localized_note(state.language, "agents.correction.action.prompt", plan, issues),
                    plan.correction_strategy,
                )
            )
        return CorrectionPatch(
            plan_id=plan.plan_id,
            agent_name=self.agent_name,
            target_version=target_version,
            operations=operations,
            rationale=plan.correction_strategy,
            expected_effect=localized_note(state.language, "agents.correction.action.effect", plan, issues),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
