from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from shotforge.core.knowledge_base import KnowledgeBase, KnowledgeEntry
from shotforge.core.project_state import ProjectState


class ContextBuildPolicy(BaseModel):
    max_chars: int = 6000
    min_source_chars: int = 120
    include_solution_summary: bool = True
    include_delivery_readiness: bool = True
    redact_terms: list[str] = Field(default_factory=lambda: ["api_key", "secret", "token"])


class ContextSource(BaseModel):
    source_id: str
    source_type: str
    title: str
    content: str
    priority: int = 50
    char_count: int = 0
    included: bool = True
    truncated: bool = False
    redacted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class BuiltContext(BaseModel):
    agent_name: str
    brief: str
    knowledge: list[KnowledgeEntry]
    sources: list[ContextSource] = Field(default_factory=list)
    max_chars: int = 6000
    char_count: int = 0
    truncated: bool = False
    digest: str = ""

    def as_prompt(self) -> str:
        source_block = "\n".join(
            f"[{item.source_type}] {item.title}: {item.content}"
            for item in self.sources
            if item.included
        )
        return f"{self.brief}\n\nContext Sources:\n{source_block}"


class ContextBuilder:
    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        policy: ContextBuildPolicy | None = None,
    ):
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.policy = policy or ContextBuildPolicy()

    def build(
        self,
        state: ProjectState,
        agent_name: str,
        tags: list[str] | None = None,
        max_chars: int | None = None,
    ) -> BuiltContext:
        policy = self.policy.model_copy(update={"max_chars": max_chars or self.policy.max_chars})
        knowledge = self.knowledge_base.search(
            query=f"{state.user_idea} {state.style} {state.target_platform}",
            tags=tags,
        )
        for ref in [entry.id for entry in knowledge]:
            if ref not in state.knowledge_refs:
                state.knowledge_refs.append(ref)

        brief = (
            f"Agent: {agent_name}\n"
            f"Idea: {self._clip(self._redact_text(state.user_idea, policy)[0], max(120, policy.max_chars // 4))}\n"
            f"Style: {state.style}\n"
            f"Language: {state.language}\n"
            f"Duration: {state.duration_seconds}s\n"
            f"Target platform: {state.target_platform}\n"
            f"Current version: {state.version}"
        )
        sources = self._redact_sources(self._build_sources(state, knowledge, policy), policy)
        packed_sources, truncated = self._pack_sources(
            sources,
            budget=policy.max_chars - len(brief) - len("\n\nContext Sources:\n"),
        )
        prompt_text = self._render_prompt(brief, packed_sources)
        return BuiltContext(
            agent_name=agent_name,
            brief=brief,
            knowledge=knowledge,
            sources=packed_sources,
            max_chars=policy.max_chars,
            char_count=len(prompt_text),
            truncated=truncated,
            digest=sha256(prompt_text.encode("utf-8")).hexdigest()[:16],
        )

    def _build_sources(
        self,
        state: ProjectState,
        knowledge: list[KnowledgeEntry],
        policy: ContextBuildPolicy,
    ) -> list[ContextSource]:
        sources = [
            ContextSource(
                source_id="user_goal",
                source_type="user_goal",
                title="User goal",
                content=state.user_idea,
                priority=100,
                char_count=len(state.user_idea),
            ),
            ContextSource(
                source_id="project_state",
                source_type="project_state",
                title="Project state summary",
                content=(
                    f"style={state.style}; language={state.language}; "
                    f"duration={state.duration_seconds}; shots={len(state.shots)}; "
                    f"prompts={len(state.prompt_package.prompts)}; version={state.version}"
                ),
                priority=95,
            ),
        ]
        for index, entry in enumerate(knowledge):
            sources.append(
                ContextSource(
                    source_id=entry.id,
                    source_type="knowledge",
                    title=entry.title,
                    content=entry.content,
                    priority=80 - index,
                    metadata={"tags": entry.tags},
                )
            )
        if policy.include_solution_summary and state.solution_architecture:
            solution = state.solution_architecture
            sources.append(
                ContextSource(
                    source_id="solution_architecture",
                    source_type="solution",
                    title="Solution architecture",
                    content=(
                        f"industry={solution.industry}; scenario={solution.scenario}; "
                        f"knowledge_assets={', '.join(solution.knowledge_assets)}"
                    ),
                    priority=70,
                )
            )
        if policy.include_delivery_readiness and state.delivery_readiness:
            readiness = state.delivery_readiness
            sources.append(
                ContextSource(
                    source_id="delivery_readiness",
                    source_type="readiness",
                    title="Delivery readiness",
                    content=(
                        f"status={readiness.overall_status}; "
                        f"checks={len(readiness.checks)}; "
                        f"next_actions={len(readiness.next_actions)}"
                    ),
                    priority=65,
                )
            )
        for source in sources:
            source.char_count = len(source.content)
        return sorted(sources, key=lambda item: item.priority, reverse=True)

    def _redact_sources(
        self,
        sources: list[ContextSource],
        policy: ContextBuildPolicy,
    ) -> list[ContextSource]:
        if not policy.redact_terms:
            return sources
        redacted_sources: list[ContextSource] = []
        for source in sources:
            item = source.model_copy(deep=True)
            redacted, was_redacted = self._redact_text(item.content, policy)
            if redacted != item.content:
                item.content = redacted
                item.redacted = was_redacted
                item.char_count = len(item.content)
            redacted_sources.append(item)
        return redacted_sources

    def _redact_text(self, text: str, policy: ContextBuildPolicy) -> tuple[str, bool]:
        if not policy.redact_terms:
            return text, False
        term_pattern = "|".join(re.escape(term) for term in policy.redact_terms)
        assignment_pattern = re.compile(
            rf"\b({term_pattern})\b\s*[:=]\s*[\w\-\.]+",
            flags=re.IGNORECASE,
        )
        bare_pattern = re.compile(rf"\b({term_pattern})\b", flags=re.IGNORECASE)
        redacted = assignment_pattern.sub("[REDACTED]", text)
        redacted = bare_pattern.sub("[REDACTED_TERM]", redacted)
        return redacted, redacted != text

    def _pack_sources(
        self,
        sources: list[ContextSource],
        budget: int,
    ) -> tuple[list[ContextSource], bool]:
        remaining = max(0, budget)
        packed: list[ContextSource] = []
        truncated_any = False
        for source in sources:
            item = source.model_copy(deep=True)
            prefix_len = len(f"[{item.source_type}] {item.title}: \n")
            if remaining <= prefix_len:
                item.included = False
                item.truncated = True
                item.content = ""
                item.char_count = 0
                truncated_any = True
                packed.append(item)
                continue
            content_budget = remaining - prefix_len
            if len(item.content) > content_budget:
                item.content = item.content[: max(0, content_budget - 3)] + "..."
                item.truncated = True
                item.char_count = len(item.content)
                truncated_any = True
            remaining -= prefix_len + item.char_count
            packed.append(item)
        return packed, truncated_any

    def _render_prompt(self, brief: str, sources: list[ContextSource]) -> str:
        source_block = "\n".join(
            f"[{item.source_type}] {item.title}: {item.content}"
            for item in sources
            if item.included
        )
        return f"{brief}\n\nContext Sources:\n{source_block}"

    def _clip(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)] + "..."

__all__ = ["BuiltContext", "ContextBuildPolicy", "ContextBuilder", "ContextSource"]
