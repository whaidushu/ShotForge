from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from shotforge.core.project_state import ProjectState
from shotforge.core.knowledge_base import KnowledgeBase, KnowledgeEntry


class BuiltContext(BaseModel):
    agent_name: str
    brief: str
    knowledge: list[KnowledgeEntry]
    bundle: "ContextBundle | None" = None

    def as_prompt(self) -> str:
        if self.bundle is not None:
            return self.bundle.as_prompt()
        knowledge_block = "\n".join(f"- {item.title}: {item.content}" for item in self.knowledge)
        return f"{self.brief}\n\nKnowledge:\n{knowledge_block}"


class ContextSource(BaseModel):
    source_id: str
    source_type: Literal[
        "user_goal",
        "project_state",
        "version",
        "evaluation",
        "redesign",
        "knowledge",
        "memory",
        "tool_result",
    ]
    title: str
    content: str
    priority: int = 50
    tokens_estimate: int = 0
    metadata: dict = Field(default_factory=dict)


class ContextWindowPolicy(BaseModel):
    max_chars: int = 8000
    reserve_chars: int = 1200
    compression: Literal["none", "truncate"] = "truncate"


class ContextBundle(BaseModel):
    agent_name: str
    policy: ContextWindowPolicy = Field(default_factory=ContextWindowPolicy)
    sources: list[ContextSource] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return sum(len(source.content) for source in self.sources)

    def as_prompt(self) -> str:
        blocks = [
            f"[{source.source_type}] {source.title}\n{source.content}"
            for source in sorted(self.sources, key=lambda item: item.priority)
        ]
        return "\n\n".join(blocks)

    def compact(self) -> "ContextBundle":
        budget = max(self.policy.max_chars - self.policy.reserve_chars, 1000)
        used = 0
        kept: list[ContextSource] = []
        for source in sorted(self.sources, key=lambda item: item.priority):
            content = source.content
            remaining = budget - used
            if remaining <= 0:
                break
            if len(content) > remaining and self.policy.compression == "truncate":
                content = content[:remaining].rstrip() + "\n[truncated]"
            kept.append(source.model_copy(update={"content": content}))
            used += len(content)
        return self.model_copy(update={"sources": kept, "metadata": {**self.metadata, "compacted": True}})


class ContextBuilder:
    def __init__(self, knowledge_base: KnowledgeBase | None = None):
        self.knowledge_base = knowledge_base or KnowledgeBase()

    def build(self, state: ProjectState, agent_name: str, tags: list[str] | None = None) -> BuiltContext:
        knowledge = self._search_knowledge(state, tags)
        bundle = self._build_bundle(state, agent_name, knowledge, tags=tags)
        brief = bundle.sources[0].content if bundle.sources else ""
        return BuiltContext(agent_name=agent_name, brief=brief, knowledge=knowledge, bundle=bundle)

    def build_bundle(
        self,
        state: ProjectState,
        agent_name: str,
        tags: list[str] | None = None,
        policy: ContextWindowPolicy | None = None,
    ) -> ContextBundle:
        knowledge = self._search_knowledge(state, tags)
        return self._build_bundle(state, agent_name, knowledge, tags=tags, policy=policy)

    def _search_knowledge(
        self,
        state: ProjectState,
        tags: list[str] | None = None,
    ) -> list[KnowledgeEntry]:
        knowledge = self.knowledge_base.search(
            query=f"{state.user_idea} {state.style} {state.target_platform}",
            tags=tags,
        )
        for ref in [entry.id for entry in knowledge]:
            if ref not in state.knowledge_refs:
                state.knowledge_refs.append(ref)
        return knowledge

    def _build_bundle(
        self,
        state: ProjectState,
        agent_name: str,
        knowledge: list[KnowledgeEntry],
        tags: list[str] | None = None,
        policy: ContextWindowPolicy | None = None,
    ) -> ContextBundle:
        brief = (
            f"Agent: {agent_name}\n"
            f"Idea: {state.user_idea}\n"
            f"Style: {state.style}\n"
            f"Language: {state.language}\n"
            f"Duration: {state.duration_seconds}s\n"
            f"Target platform: {state.target_platform}\n"
            f"Current version: {state.version}"
        )
        sources = [
            ContextSource(
                source_id="user_goal",
                source_type="user_goal",
                title="User creative goal",
                content=brief,
                priority=10,
            ),
            ContextSource(
                source_id="project_state_summary",
                source_type="project_state",
                title="Project state summary",
                content=self._state_summary(state),
                priority=20,
            ),
        ]
        if state.evaluation_reports:
            report = state.evaluation_reports[-1]
            sources.append(
                ContextSource(
                    source_id=report.evaluation_id,
                    source_type="evaluation",
                    title="Latest evaluation report",
                    content=(
                        f"overall_score={report.score_card.overall_score}; "
                        f"issues={len(report.issues)}; "
                        f"focus={', '.join(report.suggested_focus)}"
                    ),
                    priority=30,
                )
            )
        if state.redesign_plans:
            plan = state.redesign_plans[-1]
            sources.append(
                ContextSource(
                    source_id=plan.redesign_plan_id,
                    source_type="redesign",
                    title="Latest redesign plan",
                    content=plan.model_dump_json(),
                    priority=35,
                )
            )
        for entry in knowledge:
            sources.append(
                ContextSource(
                    source_id=entry.id,
                    source_type="knowledge",
                    title=entry.title,
                    content=entry.content,
                    priority=60,
                    metadata={"tags": entry.tags},
                )
            )
        bundle = ContextBundle(
            agent_name=agent_name,
            policy=policy or ContextWindowPolicy(),
            sources=sources,
            metadata={"tags": tags or [], "knowledge_count": len(knowledge)},
        )
        return bundle.compact()

    def _state_summary(self, state: ProjectState) -> str:
        return (
            f"characters={len(state.characters)}, scenes={len(state.scenes)}, "
            f"shots={len(state.shots)}, prompts={len(state.prompt_package.prompts)}, "
            f"generation_results={len(state.generation_results)}, "
            f"evaluation_reports={len(state.evaluation_reports)}, "
            f"versions={len(state.versions)}"
        )

__all__ = [
    "BuiltContext",
    "ContextBuilder",
    "ContextBundle",
    "ContextSource",
    "ContextWindowPolicy",
]
