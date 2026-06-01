from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from shotforge.config import get_settings


class MemoryRecord(BaseModel):
    memory_id: str = Field(default_factory=lambda: f"mem_{uuid4().hex[:12]}")
    kind: str = "run_summary"
    content: str
    tags: list[str] = Field(default_factory=list)
    namespace: str = "default"
    scope: str = "project"
    importance: float = Field(default=0.5, ge=0, le=1)
    access_count: int = 0
    source_run_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LocalMemoryStore:
    """JSONL memory store for local cross-run context."""

    def __init__(self, path: Path | None = None):
        self.path = path or get_settings().memory_store_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(
        self,
        content: str,
        *,
        kind: str = "run_summary",
        tags: list[str] | None = None,
        namespace: str = "default",
        scope: str = "project",
        importance: float = 0.5,
        source_run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            kind=kind,
            content=content,
            tags=tags or [],
            namespace=namespace,
            scope=scope,
            importance=importance,
            source_run_id=source_run_id,
            metadata=metadata or {},
        )
        with self.path.open("a", encoding="utf-8") as file:
            file.write(record.model_dump_json() + "\n")
        return record

    def search(
        self,
        query: str = "",
        tags: list[str] | None = None,
        limit: int = 5,
        namespace: str | None = None,
    ) -> list[MemoryRecord]:
        tag_filter = set(tags or [])
        query_terms = {term.lower() for term in query.replace(",", " ").split() if term}
        scored: list[tuple[float, MemoryRecord]] = []
        records = self._load()
        for record in records:
            if namespace and record.namespace != namespace:
                continue
            if tag_filter and not tag_filter.intersection(record.tags):
                continue
            content_lower = record.content.lower()
            term_hits = sum(1 for term in query_terms if term in content_lower)
            if query_terms and not term_hits:
                continue
            tag_hits = len(tag_filter.intersection(record.tags))
            score = term_hits + tag_hits * 2 + record.importance * 3 + record.access_count * 0.05
            scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = [record for _, record in scored[:limit]]
        if results:
            self._mark_accessed({record.memory_id for record in results}, records)
        return results

    def promote_run(
        self,
        *,
        run_id: str,
        summary: str,
        tags: list[str],
        namespace: str = "default",
        importance: float = 0.8,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        return self.add(
            summary,
            kind="promoted_run",
            tags=tags,
            namespace=namespace,
            importance=importance,
            source_run_id=run_id,
            metadata=metadata or {"promotion_reason": "successful_run"},
        )

    def _load(self) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(MemoryRecord.model_validate(json.loads(line)))
        return records

    def list_records(self) -> list[MemoryRecord]:
        return self._load()

    def _save_all(self, records: list[MemoryRecord]) -> None:
        payload = "\n".join(record.model_dump_json() for record in records)
        self.path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")

    def _mark_accessed(self, memory_ids: set[str], records: list[MemoryRecord]) -> None:
        now = datetime.now(timezone.utc)
        changed = False
        for record in records:
            if record.memory_id in memory_ids:
                record.access_count += 1
                record.last_accessed_at = now
                changed = True
        if changed:
            self._save_all(records)
