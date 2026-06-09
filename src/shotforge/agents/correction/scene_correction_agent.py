from __future__ import annotations

from shotforge.agents.correction._helpers import (
    effect_contracts_for_shot,
    localized_note,
    negative_constraints_for_issues,
    operation,
    physical_convergence_contracts,
    prompt_revision_note,
    story_beat_upgrade,
    target_issues,
    target_shot_ids,
)
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState, runtime_language


class SceneCorrectionAgent(CorrectionAgent):
    correction_type = "scene"
    agent_name = "scene_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        language = runtime_language(state)
        issues = target_issues(state, plan)
        operations = []
        for shot_id in target_shot_ids(state, plan):
            shot = next(item for item in state.shots if item.shot_id == shot_id)
            shot_issues = [issue for issue in issues if issue.shot_id == shot_id]
            contracts = [
                *effect_contracts_for_shot(shot_issues, shot_id, language),
                *physical_convergence_contracts(plan),
            ]
            contract_text = " ".join(contracts)
            scene_note = story_beat_upgrade(
                state,
                shot_id,
                "scene",
                localized_note(language, "agents.correction.scene.scene", plan, issues),
            )
            shot_note = story_beat_upgrade(
                state,
                shot_id,
                "scene",
                localized_note(language, "agents.correction.scene.shot", plan, issues),
            )
            prompt_note = prompt_revision_note(
                state,
                shot_id,
                "scene",
                localized_note(language, "agents.correction.scene.prompt", plan, issues),
            )
            operations.append(
                operation(
                    "append_scene_description",
                    shot.scene_id,
                    f"scenes[{shot.scene_id}].description",
                    scene_note,
                    plan.correction_strategy,
                )
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
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    " ".join(
                        [
                            prompt_note,
                            contract_text,
                        ]
                    ).strip(),
                    plan.correction_strategy,
                    metadata={"effect_contract": True},
                )
            )
            if contract_text:
                operations.append(
                    operation(
                        "append_structured_template_text",
                        shot_id,
                        f"prompt_package.prompts[{shot_id}].structured_template.scene_constraints",
                        contract_text,
                        plan.correction_strategy,
                        metadata={"effect_contract": True},
                    )
                )
                operations.append(
                    operation(
                        "append_structured_template_text",
                        shot_id,
                        f"prompt_package.prompts[{shot_id}].structured_template.style_constraints",
                        contract_text,
                        plan.correction_strategy,
                        metadata={"effect_contract": True},
                    )
                )
                operations.append(
                    operation(
                        "append_structured_template_list",
                        shot_id,
                        f"prompt_package.prompts[{shot_id}].structured_template.physical_constraints",
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
            expected_effect=localized_note(language, "agents.correction.scene.effect", plan, issues),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
