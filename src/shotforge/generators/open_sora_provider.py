from __future__ import annotations

from shotforge.generators.planned_provider import PlannedGeneratorProvider


class OpenSoraProvider(PlannedGeneratorProvider):
    def __init__(self) -> None:
        super().__init__("open_sora", "Open-Sora Provider", cost_mode="local")
