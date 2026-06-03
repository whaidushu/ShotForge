from __future__ import annotations

from pydantic import BaseModel, Field

from shotforge.core.project_state import ProjectState
from shotforge.core.runtime_models import MemorySelectionRecord
from shotforge.infra.memory.store import LocalMemoryStore, MemoryRecord


class MemoryGovernancePolicy(BaseModel):
    policy_id: str = "default_memory_governance_policy"
    namespace: str = "shotforge"
    allowed_namespaces: list[str] = Field(default_factory=lambda: ["default", "shotforge"])
    max_hits_per_agent: int = 3
    min_importance: float = 0.2
    allowed_kinds: list[str] = Field(default_factory=lambda: ["run_summary", "promoted_run"])
    promote_agents: list[str] = Field(default_factory=lambda: ["delivery_readiness_agent", "export_agent"])
    promote_min_shots: int = 1
    promote_on_readiness: list[str] = Field(default_factory=lambda: ["passed", "warning"])


class MemoryManager:
    def __init__(
        self,
        store: LocalMemoryStore | None = None,
        policy: MemoryGovernancePolicy | None = None,
    ) -> None:
        self.store = store or LocalMemoryStore()
        self.policy = policy or MemoryGovernancePolicy()

    def select(
        self,
        state: ProjectState,
        agent_name: str,
        *,
        tags: list[str] | None = None,
        query: str | None = None,
    ) -> tuple[list[MemoryRecord], MemorySelectionRecord]:
        query = query or state.user_idea
        tags = tags or []
        candidates = [
            record
            for record in self.store.list_records()
            if record.namespace in self.policy.allowed_namespaces
            and record.importance >= self.policy.min_importance
            and record.kind in self.policy.allowed_kinds
        ]
        hits = self._search_allowed_namespaces(query=query, tags=tags)
        allowed_ids = {record.memory_id for record in candidates}
        selected = [record for record in hits if record.memory_id in allowed_ids]
        selected_ids = {record.memory_id for record in selected}
        record = MemorySelectionRecord(
            agent_name=agent_name,
            query=query,
            tags=tags,
            namespace=",".join(self.policy.allowed_namespaces),
            candidate_count=len(candidates),
            selected_memory_ids=[item.memory_id for item in selected],
            rejected_memory_ids=[
                item.memory_id for item in candidates if item.memory_id not in selected_ids
            ],
            reasons=self._selection_reasons(selected, candidates),
            policy=self.policy.model_dump(mode="json"),
        )
        return selected, record

    def _search_allowed_namespaces(self, *, query: str, tags: list[str]) -> list[MemoryRecord]:
        hits: list[MemoryRecord] = []
        seen: set[str] = set()
        for namespace in self.policy.allowed_namespaces:
            for record in self.store.search(
                query=query,
                tags=tags,
                limit=self.policy.max_hits_per_agent,
                namespace=namespace,
            ):
                if record.memory_id in seen:
                    continue
                seen.add(record.memory_id)
                hits.append(record)
        return hits[: self.policy.max_hits_per_agent]

    def should_promote(self, state: ProjectState, agent_name: str) -> MemorySelectionRecord:
        reasons: list[str] = []
        decision = "promote"
        if agent_name not in self.policy.promote_agents:
            decision = "not_applicable"
            reasons.append("agent_not_configured_for_promotion")
        if decision == "promote" and len(state.shots) < self.policy.promote_min_shots:
            decision = "skip"
            reasons.append("insufficient_shot_count")
        if decision == "promote" and state.delivery_readiness:
            readiness = state.delivery_readiness.overall_status
            if readiness not in self.policy.promote_on_readiness:
                decision = "skip"
                reasons.append(f"readiness_not_promotable:{readiness}")
        elif decision == "promote" and agent_name == "export_agent":
            decision = "skip"
            reasons.append("delivery_readiness_missing")
        if decision == "promote" and state.metadata.get("memory_promoted_run_id") == state.run_id:
            decision = "skip"
            reasons.append("run_already_promoted")
        return MemorySelectionRecord(
            agent_name=agent_name,
            query=state.user_idea,
            tags=[state.style, state.target_platform, "shotforge-run"],
            namespace=self.policy.namespace,
            promotion_decision=decision,  # type: ignore[arg-type]
            reasons=reasons or ["promotion_policy_passed"],
            policy=self.policy.model_dump(mode="json"),
            metadata={"run_id": state.run_id, "project_id": state.project_id},
        )

    def promote_run(self, state: ProjectState, agent_name: str) -> tuple[MemoryRecord | None, MemorySelectionRecord]:
        decision = self.should_promote(state, agent_name)
        if decision.promotion_decision != "promote":
            return None, decision
        summary = (
            f"Run {state.run_id}: idea={state.user_idea}; style={state.style}; "
            f"shots={len(state.shots)}; prompts={len(state.prompt_package.prompts)}; "
            f"readiness={state.delivery_readiness.overall_status if state.delivery_readiness else 'n/a'}"
        )
        record = self.store.promote_run(
            run_id=state.run_id,
            summary=summary,
            tags=decision.tags,
            namespace=self.policy.namespace,
            importance=0.75,
            metadata={
                "project_id": state.project_id,
                "version": state.version,
                "export_count": len(state.exports),
                "promotion_agent": agent_name,
                "promotion_policy_id": self.policy.policy_id,
            },
        )
        decision.selected_memory_ids = [record.memory_id]
        return record, decision

    def _selection_reasons(
        self,
        selected: list[MemoryRecord],
        candidates: list[MemoryRecord],
    ) -> list[str]:
        if selected:
            return ["query_tag_importance_match"]
        if candidates:
            return ["candidates_available_but_not_relevant"]
        return ["no_policy_eligible_memory"]


__all__ = ["MemoryGovernancePolicy", "MemoryManager"]
