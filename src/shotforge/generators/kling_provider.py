from __future__ import annotations

from shotforge.generators.planned_provider import PlannedGeneratorProvider


class KlingProvider(PlannedGeneratorProvider):
    def __init__(self) -> None:
        super().__init__("kling", "Kling Provider", cost_mode="paid")
