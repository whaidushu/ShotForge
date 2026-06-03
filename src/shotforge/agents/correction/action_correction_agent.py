from __future__ import annotations

from shotforge.agents.correction._helpers import (
    effect_contracts_for_shot,
    localized_note,
    negative_constraints_for_issues,
    operation,
    prompt_revision_note,
    story_beat_upgrade,
    target_issues,
    target_shot_ids,
)
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState, runtime_language


class ActionCorrectionAgent(CorrectionAgent):
    correction_type = "action"
    agent_name = "action_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        language = runtime_language(state)
        issues = target_issues(state, plan)
        note = localized_note(language, "agents.correction.action.note", plan, issues)
        operations = []
        for shot_id in target_shot_ids(state, plan):
            shot_issues = [issue for issue in issues if issue.shot_id == shot_id]
            contracts = effect_contracts_for_shot(shot_issues, shot_id, language)
            contract_text = " ".join(contracts)
            shot_note = story_beat_upgrade(state, shot_id, "action", note)
            motion_note = story_beat_upgrade(
                state,
                shot_id,
                "action",
                localized_note(language, "agents.correction.action.motion", plan, issues),
            )
            prompt_note = prompt_revision_note(
                state,
                shot_id,
                "action",
                localized_note(language, "agents.correction.action.prompt", plan, issues),
            )
            operations.append(
                operation(
                    "append_shot_description",
                    shot_id,
                    f"shots[{shot_id}].description",
                    shot_note,
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_motion_subject",
                    shot_id,
                    f"shots[{shot_id}].motion.subject_motion",
                    " ".join(
                        [
                            motion_note,
                            contract_text,
                        ]
                    ).strip(),
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_structured_template_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].structured_template.action_sequence",
                    contract_text,
                    plan.correction_strategy,
                    metadata={"effect_contract": True},
                )
            )
            operations.append(
                operation(
                    "append_structured_template_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].structured_template.motion_direction",
                    "Use a continuous readable trajectory: start pose -> single movement path -> end pose.",
                    plan.correction_strategy,
                    metadata={"effect_contract": True},
                )
            )
            operations.append(
                operation(
                    "append_structured_template_list",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].structured_template.success_criteria",
                    [
                        "the same action remains continuous from first frame to last frame",
                        "the viewer can identify the start pose, movement direction, and end pose",
                    ],
                    plan.correction_strategy,
                    metadata={"effect_contract": True},
                )
            )
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    " ".join(
                        [
                            prompt_note,
                            contract_text,
                            "Use: start pose -> continuous movement -> end pose.",
                        ]
                    ).strip(),
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
            expected_effect=localized_note(language, "agents.correction.action.effect", plan, issues),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
