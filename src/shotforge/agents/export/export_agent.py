from __future__ import annotations

from shotforge.core.project_state import ProjectState
from shotforge.core.trace_log import TraceLog
from shotforge.skills import SkillRegistry


def export_agent(state: ProjectState, registry: SkillRegistry) -> ProjectState:
    with TraceLog(state).span("export_agent"):
        registry.call("export.json", state)
        registry.call("export.csv", state)
        registry.call("export.markdown", state)
        registry.call("version.save_snapshot", state, "exported")
    return state
