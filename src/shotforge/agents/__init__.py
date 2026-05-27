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
from shotforge.core.harness_runtime import AgentHarnessRuntime
from shotforge.core.project_state import ProjectState
from shotforge.core.version_manager import VersionManager
from shotforge.exporters import ExportManager
from shotforge.mock_llm import MockLLM
from shotforge.skills import SkillRegistry, SkillSpec


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(
        "mock_llm.complete",
        MockLLM().complete,
        SkillSpec(
            name="mock_llm.complete",
            description="Deterministic local LLM completion for POC agent reasoning.",
            permission_scope="local_inference",
        ),
    )
    registry.register(
        "export.json",
        ExportManager().export_json,
        SkillSpec(name="export.json", description="Export full ProjectState as JSON.", permission_scope="file_write"),
    )
    registry.register(
        "export.csv",
        ExportManager().export_csv,
        SkillSpec(name="export.csv", description="Export storyboard package as CSV.", permission_scope="file_write"),
    )
    registry.register(
        "export.markdown",
        ExportManager().export_markdown,
        SkillSpec(name="export.markdown", description="Export readable package as Markdown.", permission_scope="file_write"),
    )
    registry.register(
        "version.save_snapshot",
        VersionManager().save_snapshot,
        SkillSpec(
            name="version.save_snapshot",
            description="Persist a versioned ProjectState snapshot.",
            permission_scope="file_write",
        ),
    )
    return registry


class AgentHarness:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        registry: SkillRegistry | None = None,
        runtime: AgentHarnessRuntime | None = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.registry = registry or build_default_registry()
        self.runtime = runtime or AgentHarnessRuntime(self.context_builder, self.registry)

    def intent_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "intent_agent",
            lambda project: intent_agent(project, self.context_builder, self.registry),
            tags=["intent", "creative"],
        )

    def storyboard_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "storyboard_agent",
            lambda project: storyboard_agent(project, self.context_builder),
            tags=["storyboard", "structure"],
        )

    def motion_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "motion_agent",
            lambda project: motion_agent(project, self.context_builder),
            tags=["motion", "camera"],
        )

    def audio_cue_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "audio_cue_agent",
            lambda project: audio_cue_agent(project, self.context_builder),
            tags=["audio", "sound"],
        )

    def prompt_adapter_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "prompt_adapter_agent",
            lambda project: prompt_adapter_agent(project, self.context_builder),
            tags=["prompt", "video-model"],
        )

    def export_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "export_agent",
            lambda project: export_agent(project, self.registry),
            tags=["export", "artifact"],
        )


__all__ = ["AgentHarness", "build_default_registry"]
