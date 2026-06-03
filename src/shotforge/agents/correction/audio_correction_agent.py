from __future__ import annotations

from shotforge.agents.correction._helpers import (
    localized_note,
    operation,
    prompt_revision_note,
    story_beat_upgrade,
    target_issues,
    target_shot_ids,
)
from shotforge.agents.correction.base import CorrectionAgent
from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState, runtime_language


class AudioCorrectionAgent(CorrectionAgent):
    correction_type = "audio"
    agent_name = "audio_correction_agent"

    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        language = runtime_language(state)
        issues = target_issues(state, plan)
        operations = []
        for shot_id in target_shot_ids(state, plan):
            sound_note = story_beat_upgrade(
                state,
                shot_id,
                "audio",
                localized_note(language, "agents.correction.audio.sound", plan, issues),
            )
            prompt_note = prompt_revision_note(
                state,
                shot_id,
                "audio",
                localized_note(language, "agents.correction.audio.prompt", plan, issues),
            )
            operations.append(
                operation(
                    "append_audio_sound_design",
                    shot_id,
                    f"audio_cues[{shot_id}].sound_design",
                    [sound_note],
                    plan.correction_strategy,
                )
            )
            operations.append(
                operation(
                    "append_prompt_text",
                    shot_id,
                    f"prompt_package.prompts[{shot_id}].prompt",
                    prompt_note,
                    plan.correction_strategy,
                )
            )
        return CorrectionPatch(
            plan_id=plan.plan_id,
            agent_name=self.agent_name,
            target_version=target_version,
            operations=operations,
            rationale=plan.correction_strategy,
            expected_effect=localized_note(language, "agents.correction.audio.effect", plan, issues),
            risk=plan.risk,
            metadata={"correction_type": self.correction_type},
        )
