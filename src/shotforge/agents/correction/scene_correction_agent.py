from __future__ import annotations

from shotforge.agents.correction._helpers import localized_note, operation, target_issues, target_shot_ids
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState


class SceneCorrectionAgent(CorrectionAgent):
    correction_type = "scene"
    agent_name = "scene_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        issues = target_issues(state, plan)
        operations = []
        for shot_id in target_shot_ids(state, plan):
            shot = next(item for item in state.shots if item.shot_id == shot_id)
            operations.append(
                operation(
                    "append_scene_description",
                    shot.scene_id,
                    f"scenes[{shot.scene_id}].description",
                    localized_note(state.language, "agents.correction.scene.scene", plan, issues),
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_shot_description",
                    shot_id,
                    f"shots[{shot_id}].description",
                    localized_note(state.language, "agents.correction.scene.shot", plan, issues),
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    localized_note(state.language, "agents.correction.scene.prompt", plan, issues),
                    plan.correction_strategy,
                )
            )
        return CorrectionPatch(
            plan_id=plan.plan_id,
            agent_name=self.agent_name,
            target_version=target_version,
            operations=operations,
            rationale=plan.correction_strategy,
            expected_effect=localized_note(state.language, "agents.correction.scene.effect", plan, issues),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
