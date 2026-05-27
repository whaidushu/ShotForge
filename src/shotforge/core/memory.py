from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    memory_id: str = Field(default_factory=lambda: f"mem_{uuid4().hex[:12]}")
    scope: str = "project"
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class InMemoryStore:
    def __init__(self):
        self._entries: list[MemoryEntry] = []

    def add(self, content: str, tags: list[str] | None = None, scope: str = "project") -> MemoryEntry:
        entry = MemoryEntry(content=content, tags=tags or [], scope=scope)
        self._entries.append(entry)
        return entry

    def search(self, query: str = "", tags: list[str] | None = None, limit: int = 5) -> list[MemoryEntry]:
        tag_filter = set(tags or [])
        results = []
        for entry in self._entries:
            if tag_filter and not tag_filter.intersection(entry.tags):
                continue
            if query and query.lower() not in entry.content.lower():
                continue
            results.append(entry)
        return results[:limit]


__all__ = ["InMemoryStore", "MemoryEntry"]
