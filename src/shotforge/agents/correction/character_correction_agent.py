from __future__ import annotations

from shotforge.agents.correction._helpers import localized_note, operation, target_issues, target_shot_ids
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState


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
                localized_note(state.language, "agents.correction.character.behavior", plan, issues),
                plan.correction_strategy,
            )
        )
        for shot_id in target_shot_ids(state, plan):
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    localized_note(state.language, "agents.correction.character.prompt", plan, issues),
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
                state.language, "agents.correction.character.effect", plan, issues
            ),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
