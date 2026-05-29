"""Agent modules for design, evaluation, correction, structuring, and export."""

from __future__ import annotations

from shotforge.agents.design import (
    audio_cue_agent,
    delivery_readiness_agent,
    intent_agent,
    motion_agent,
    prompt_adapter_agent,
    solution_architect_agent,
    storyboard_agent,
)
from shotforge.agents.export import export_agent
from shotforge.core.agent_catalog import AgentCatalog, AgentSpec
from shotforge.core.context_builder import ContextBuilder
from shotforge.core.harness_runtime import AgentHarnessRuntime
from shotforge.core.project_state import ProjectState
from shotforge.core.version_manager import VersionManager
from shotforge.exporters import ExportManager
from shotforge.mock_llm import MockLLM
from shotforge.skills import SkillRegistry


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(
        "mock_llm.complete",
        MockLLM().complete,
        description="Deterministic local mock LLM completion.",
        permission_scope="local_inference",
        risk_level="low",
    )
    registry.register(
        "export.json",
        ExportManager().export_json,
        description="Export ProjectState as JSON.",
        permission_scope="local_file_write",
        risk_level="medium",
    )
    registry.register(
        "export.csv",
        ExportManager().export_csv,
        description="Export storyboard as CSV.",
        permission_scope="local_file_write",
        risk_level="medium",
    )
    registry.register(
        "export.markdown",
        ExportManager().export_markdown,
        description="Export production package as Markdown.",
        permission_scope="local_file_write",
        risk_level="medium",
    )
    registry.register(
        "export.manifest",
        ExportManager().export_manifest,
        description="Export customer handoff manifest.",
        permission_scope="local_file_write",
        risk_level="medium",
    )
    registry.register(
        "export.trace",
        ExportManager().export_trace,
        description="Export trace and harness audit JSON.",
        permission_scope="local_file_write",
        risk_level="medium",
    )
    registry.register(
        "export.run_summary",
        ExportManager().export_run_summary,
        description="Export customer-facing run summary.",
        permission_scope="local_file_write",
        risk_level="medium",
    )
    registry.register(
        "version.save_snapshot",
        VersionManager().save_snapshot,
        description="Persist a version snapshot.",
        permission_scope="local_file_write",
        risk_level="medium",
    )
    return registry


def build_default_agent_catalog() -> AgentCatalog:
    return AgentCatalog(
        [
            AgentSpec(
                agent_name="intent_agent",
                role="Extract creative intent and primary subject constraints.",
                inputs=["user_idea", "style", "language"],
                outputs=["creative_intent", "characters"],
                skills=["mock_llm.complete"],
                context_tags=["cinematic", "visual"],
                extension_points=["real_llm_provider", "customer_brief_parser"],
            ),
            AgentSpec(
                agent_name="storyboard_agent",
                role="Create scenes and shots from the creative intent.",
                inputs=["creative_intent", "duration_seconds"],
                outputs=["scenes", "shots"],
                dependencies=["intent_agent"],
                context_tags=["short-form", "pacing"],
                extension_points=["storyboard_template_library"],
            ),
            AgentSpec(
                agent_name="motion_agent",
                role="Attach camera movement, subject motion, transition, and pacing.",
                inputs=["shots"],
                outputs=["shot.motion"],
                dependencies=["storyboard_agent"],
                context_tags=["motion", "pacing"],
                extension_points=["motion_template_library"],
            ),
            AgentSpec(
                agent_name="audio_cue_agent",
                role="Generate music and sound design cues per shot.",
                inputs=["shots"],
                outputs=["audio_cues"],
                dependencies=["motion_agent"],
                context_tags=["audio", "sound-design"],
                extension_points=["audio_provider", "music_policy"],
            ),
            AgentSpec(
                agent_name="prompt_adapter_agent",
                role="Transform production state into provider-ready structured prompts.",
                inputs=["shots", "motion_plan", "audio_cues"],
                outputs=["prompt_package"],
                dependencies=["audio_cue_agent"],
                context_tags=["prompt", "video-model"],
                extension_points=["provider_prompt_adapter", "negative_prompt_policy"],
            ),
            AgentSpec(
                agent_name="solution_architect_agent",
                role="Translate the run into customer-facing solution architecture.",
                inputs=["prompt_package", "industry_playbooks"],
                outputs=["solution_architecture"],
                dependencies=["prompt_adapter_agent"],
                skills=["mock_llm.complete"],
                context_tags=["solution-design", "agent-infra", "customer-value"],
                extension_points=["customer_playbook_overlay", "rag_knowledge_source"],
            ),
            AgentSpec(
                agent_name="delivery_readiness_agent",
                role="Evaluate POC readiness gates and handoff requirements.",
                inputs=["project_state", "solution_architecture", "skill_registry"],
                outputs=["delivery_readiness"],
                dependencies=["solution_architect_agent"],
                context_tags=["poc-readiness", "deployment", "governance"],
                extension_points=["customer_gate_policy", "security_review_policy"],
            ),
            AgentSpec(
                agent_name="export_agent",
                role="Persist production package and handoff artifacts.",
                inputs=["project_state"],
                outputs=["exports", "versions"],
                dependencies=["delivery_readiness_agent"],
                skills=[
                    "export.json",
                    "export.csv",
                    "export.markdown",
                    "export.manifest",
                    "export.trace",
                    "export.run_summary",
                    "version.save_snapshot",
                ],
                context_tags=["export"],
                extension_points=["object_storage_exporter", "webhook_delivery"],
            ),
        ]
    )


class AgentHarness:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        registry: SkillRegistry | None = None,
        runtime: AgentHarnessRuntime | None = None,
        agent_catalog: AgentCatalog | None = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.registry = registry or build_default_registry()
        self.agent_catalog = agent_catalog or build_default_agent_catalog()
        self.runtime = runtime or AgentHarnessRuntime(
            context_builder=self.context_builder,
            registry=self.registry,
            agent_catalog=self.agent_catalog,
        )

    def intent_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "intent_agent",
            lambda project: intent_agent(project, self.context_builder, self.registry),
            tags=["cinematic", "visual"],
        )

    def storyboard_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "storyboard_agent",
            lambda project: storyboard_agent(project, self.context_builder),
            tags=["short-form", "pacing"],
        )

    def motion_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "motion_agent",
            lambda project: motion_agent(project, self.context_builder),
            tags=["motion", "pacing"],
        )

    def audio_cue_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "audio_cue_agent",
            lambda project: audio_cue_agent(project, self.context_builder),
            tags=["audio", "sound-design"],
        )

    def prompt_adapter_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "prompt_adapter_agent",
            lambda project: prompt_adapter_agent(project, self.context_builder),
            tags=["prompt", "video-model"],
        )

    def solution_architect_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "solution_architect_agent",
            lambda project: solution_architect_agent(
                project,
                self.context_builder,
                self.registry,
            ),
            tags=["solution-design", "agent-infra", "customer-value"],
        )

    def delivery_readiness_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "delivery_readiness_agent",
            lambda project: delivery_readiness_agent(
                project,
                self.context_builder,
                self.registry,
            ),
            tags=["poc-readiness", "deployment", "governance"],
        )

    def export_agent(self, state: ProjectState) -> ProjectState:
        return self.runtime.run_agent(
            state,
            "export_agent",
            lambda project: export_agent(project, self.registry),
            tags=["export"],
        )


__all__ = ["AgentHarness", "build_default_agent_catalog", "build_default_registry"]
