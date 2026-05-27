from __future__ import annotations

from shotforge.generators.planned_provider import PlannedGeneratorProvider


class RunwayProvider(PlannedGeneratorProvider):
    def __init__(self) -> None:
        super().__init__("runway", "Runway Provider", cost_mode="paid")
