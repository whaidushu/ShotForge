from __future__ import annotations

from shotforge.agents.correction._helpers import localized_note, operation, target_issues, target_shot_ids
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState


class EmotionCorrectionAgent(CorrectionAgent):
    correction_type = "emotion"
    agent_name = "emotion_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        issues = target_issues(state, plan)
        operations = []
        for shot_id in target_shot_ids(state, plan):
            scene_id = next(
                (shot.scene_id for shot in state.shots if shot.shot_id == shot_id),
                "",
            )
            if scene_id:
                operations.append(
                    operation(
                        "append_scene_emotional_goal",
                        scene_id,
                        f"scenes[{scene_id}].emotional_goal",
                        localized_note(state.language, "agents.correction.emotion.scene", plan, issues),
                        plan.correction_strategy,
                    )
                )
            operations.append(
                operation(
                    "append_shot_description",
                    shot_id,
                    f"shots[{shot_id}].description",
                    localized_note(state.language, "agents.correction.emotion.shot", plan, issues),
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    localized_note(state.language, "agents.correction.emotion.prompt", plan, issues),
                    plan.correction_strategy,
                )
            )
        return CorrectionPatch(
            plan_id=plan.plan_id,
            agent_name=self.agent_name,
            target_version=target_version,
            operations=operations,
            rationale=plan.correction_strategy,
            expected_effect=localized_note(state.language, "agents.correction.emotion.effect", plan, issues),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
