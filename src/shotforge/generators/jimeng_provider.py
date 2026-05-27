from __future__ import annotations

from shotforge.generators.planned_provider import PlannedGeneratorProvider


class JimengProvider(PlannedGeneratorProvider):
    def __init__(self) -> None:
        super().__init__("jimeng", "Jimeng Provider", cost_mode="paid")
