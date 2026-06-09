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


class CharacterCorrectionAgent(CorrectionAgent):
    correction_type = "character"
    agent_name = "character_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        issues = target_issues(state, plan)
        operations = []
        target_character = state.characters[0].character_id if state.characters else "char_primary"
        operations.append(
            operation(
                "append_character_behavior",
                target_character,
                f"characters[{target_character}].behavior_notes",
                localized_note(runtime_language(state), "agents.correction.character.behavior", plan, issues),
                plan.correction_strategy,
            )
        )
        for shot_id in target_shot_ids(state, plan):
            shot_issues = [issue for issue in issues if issue.shot_id == shot_id]
            contracts = [
                *effect_contracts_for_shot(shot_issues, shot_id, runtime_language(state)),
                *physical_convergence_contracts(plan),
            ]
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    " ".join(
                        [
                            localized_note(
                                runtime_language(state),
                                "agents.correction.character.prompt",
                                plan,
                                issues,
                            ),
                            *contracts,
                        ]
                    ).strip(),
                    plan.correction_strategy,
                    metadata={"effect_contract": bool(contracts)},
                )
            )
            if contracts:
                operations.append(
                    operation(
                        "append_structured_template_text",
                        shot_id,
                        f"prompt_package.prompts[{shot_id}].structured_template.character_identity",
                        " ".join(contracts),
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
            expected_effect=localized_note(
                runtime_language(state), "agents.correction.character.effect", plan, issues
            ),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
