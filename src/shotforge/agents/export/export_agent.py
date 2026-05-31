from __future__ import annotations

from shotforge.core.project_state import ProjectState
from shotforge.core.trace_log import TraceLog
from shotforge.skills import SkillRegistry


def export_agent(state: ProjectState, registry: SkillRegistry) -> ProjectState:
    with TraceLog(state).span("export_agent"):
        registry.call("export.csv", state, agent_name="export_agent", expected_output="csv artifact")
        registry.call(
            "export.markdown",
            state,
            agent_name="export_agent",
            expected_output="markdown artifact",
        )
        registry.call(
            "export.manifest",
            state,
            agent_name="export_agent",
            expected_output="handoff manifest",
        )
        registry.call(
            "export.package_view",
            state,
            agent_name="export_agent",
            expected_output="domain package view",
        )
        registry.call("export.trace", state, agent_name="export_agent", expected_output="trace json")
        registry.call(
            "export.run_summary",
            state,
            agent_name="export_agent",
            expected_output="run summary markdown",
        )
        registry.call("export.json", state, agent_name="export_agent", expected_output="json package")
        registry.call(
            "version.save_snapshot",
            state,
            "exported",
            agent_name="export_agent",
            expected_output="version snapshot",
        )
    return state
