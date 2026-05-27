"""Agent modules for design, evaluation, correction, structuring, and export."""

from __future__ import annotations

from shotforge.agents.design import (
    audio_cue_agent,
    intent_agent,
    motion_agent,
    prompt_adapter_agent,
    storyboard_agent,
)
from shotforge.agents.export import export_agent
from shotforge.core.context_builder import ContextBuilder
from shotforge.core.project_state import ProjectState
from shotforge.core.version_manager import VersionManager
from shotforge.exporters import ExportManager
from shotforge.mock_llm import MockLLM
from shotforge.skills import SkillRegistry


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register("mock_llm.complete", MockLLM().complete)
    registry.register("export.json", ExportManager().export_json)
    registry.register("export.csv", ExportManager().export_csv)
    registry.register("export.markdown", ExportManager().export_markdown)
    registry.register("version.save_snapshot", VersionManager().save_snapshot)
    return registry


class AgentHarness:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        registry: SkillRegistry | None = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.registry = registry or build_default_registry()

    def intent_agent(self, state: ProjectState) -> ProjectState:
        return intent_agent(state, self.context_builder, self.registry)

    def storyboard_agent(self, state: ProjectState) -> ProjectState:
        return storyboard_agent(state, self.context_builder)

    def motion_agent(self, state: ProjectState) -> ProjectState:
        return motion_agent(state, self.context_builder)

    def audio_cue_agent(self, state: ProjectState) -> ProjectState:
        return audio_cue_agent(state, self.context_builder)

    def prompt_adapter_agent(self, state: ProjectState) -> ProjectState:
        return prompt_adapter_agent(state, self.context_builder)

    def export_agent(self, state: ProjectState) -> ProjectState:
        return export_agent(state, self.registry)


__all__ = ["AgentHarness", "build_default_registry"]
