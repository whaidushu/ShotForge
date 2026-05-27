from __future__ import annotations

from shotforge.agents.correction.base import CorrectionAgent


class CorrectionAgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, CorrectionAgent] = {}

    def register(self, agent: CorrectionAgent) -> None:
        self._agents[agent.correction_type] = agent

    def get(self, correction_type: str) -> CorrectionAgent | None:
        return self._agents.get(correction_type)

    def list(self) -> list[str]:
        return sorted(self._agents)


def build_default_correction_registry() -> CorrectionAgentRegistry:
    from shotforge.agents.correction.action_correction_agent import ActionCorrectionAgent
    from shotforge.agents.correction.audio_correction_agent import AudioCorrectionAgent
    from shotforge.agents.correction.camera_correction_agent import CameraCorrectionAgent
    from shotforge.agents.correction.character_correction_agent import CharacterCorrectionAgent
    from shotforge.agents.correction.emotion_correction_agent import EmotionCorrectionAgent
    from shotforge.agents.correction.prompt_correction_agent import PromptCorrectionAgent
    from shotforge.agents.correction.scene_correction_agent import SceneCorrectionAgent

    registry = CorrectionAgentRegistry()
    registry.register(ActionCorrectionAgent())
    registry.register(AudioCorrectionAgent())
    registry.register(CameraCorrectionAgent())
    registry.register(CharacterCorrectionAgent())
    registry.register(EmotionCorrectionAgent())
    registry.register(PromptCorrectionAgent())
    registry.register(SceneCorrectionAgent())
    return registry
