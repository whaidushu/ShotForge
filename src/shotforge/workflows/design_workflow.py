from __future__ import annotations

import warnings
from typing import TypedDict

from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.filterwarnings(
    "ignore",
    message="The default value of `allowed_objects` will change.*",
    category=LangChainPendingDeprecationWarning,
)

from langgraph.graph import END, StateGraph  # noqa: E402

from shotforge.agents import AgentHarness  # noqa: E402
from shotforge.core.project_state import (  # noqa: E402
    OutputLanguage,
    ProjectState,
    set_runtime_language,
)


class WorkflowState(TypedDict):
    project: ProjectState


def build_design_graph(harness: AgentHarness | None = None):
    harness = harness or AgentHarness()
    graph = StateGraph(WorkflowState)

    def wrap(method_name: str):
        def node(workflow_state: WorkflowState) -> WorkflowState:
            method = getattr(harness, method_name)
            return {"project": method(workflow_state["project"])}

        return node

    graph.add_node("intent", wrap("intent_agent"))
    graph.add_node("storyboard", wrap("storyboard_agent"))
    graph.add_node("motion", wrap("motion_agent"))
    graph.add_node("audio", wrap("audio_cue_agent"))
    graph.add_node("prompt_adapter", wrap("prompt_adapter_agent"))
    graph.add_node("solution_architect", wrap("solution_architect_agent"))
    graph.add_node("delivery_readiness", wrap("delivery_readiness_agent"))
    graph.add_node("export", wrap("export_agent"))

    graph.set_entry_point("intent")
    graph.add_edge("intent", "storyboard")
    graph.add_edge("storyboard", "motion")
    graph.add_edge("motion", "audio")
    graph.add_edge("audio", "prompt_adapter")
    graph.add_edge("prompt_adapter", "solution_architect")
    graph.add_edge("solution_architect", "delivery_readiness")
    graph.add_edge("delivery_readiness", "export")
    graph.add_edge("export", END)
    return graph.compile()


def run_design_pipeline(
    idea: str,
    style: str = "cinematic",
    duration_seconds: int = 24,
    language: OutputLanguage = "zh",
) -> ProjectState:
    state = ProjectState(
        user_idea=idea,
        style=style,
        duration_seconds=duration_seconds,
    )
    set_runtime_language(state, language)
    result = build_design_graph().invoke({"project": state})
    project = result["project"]
    if isinstance(project, ProjectState):
        return project
    return ProjectState.model_validate(project)
