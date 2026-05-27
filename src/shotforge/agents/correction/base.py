from __future__ import annotations

from abc import ABC, abstractmethod

from shotforge.core.project_state import CorrectionPatch, CorrectionPlan, ProjectState


class CorrectionAgent(ABC):
    correction_type: str
    agent_name: str

    @abstractmethod
    def apply(self, state: ProjectState, plan: CorrectionPlan, target_version: int) -> CorrectionPatch:
        """Create a structured patch. Agents do not mutate ProjectState directly."""
