from __future__ import annotations

from pydantic import BaseModel

from shotforge.core.project_state import ProjectState
from shotforge.core.knowledge_base import KnowledgeBase, KnowledgeEntry


class BuiltContext(BaseModel):
    agent_name: str
    brief: str
    knowledge: list[KnowledgeEntry]

    def as_prompt(self) -> str:
        knowledge_block = "\n".join(f"- {item.title}: {item.content}" for item in self.knowledge)
        return f"{self.brief}\n\nKnowledge:\n{knowledge_block}"


class ContextBuilder:
    def __init__(self, knowledge_base: KnowledgeBase | None = None):
        self.knowledge_base = knowledge_base or KnowledgeBase()

    def build(self, state: ProjectState, agent_name: str, tags: list[str] | None = None) -> BuiltContext:
        knowledge = self.knowledge_base.search(
            query=f"{state.user_idea} {state.style} {state.target_platform}",
            tags=tags,
        )
        for ref in [entry.id for entry in knowledge]:
            if ref not in state.knowledge_refs:
                state.knowledge_refs.append(ref)

        brief = (
            f"Agent: {agent_name}\n"
            f"Idea: {state.user_idea}\n"
            f"Style: {state.style}\n"
            f"Language: {state.language}\n"
            f"Duration: {state.duration_seconds}s\n"
            f"Target platform: {state.target_platform}\n"
            f"Current version: {state.version}"
        )
        return BuiltContext(agent_name=agent_name, brief=brief, knowledge=knowledge)

__all__ = ["BuiltContext", "ContextBuilder"]
