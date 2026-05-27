from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

from shotforge.config import get_settings


class KnowledgeEntry(BaseModel):
    id: str
    tags: list[str] = Field(default_factory=list)
    title: str
    content: str


DEFAULT_KNOWLEDGE = [
    KnowledgeEntry(
        id="style.cinematic",
        tags=["cinematic", "visual", "lighting"],
        title="Cinematic Visual Baseline",
        content="Use clear subject focus, motivated lighting, layered depth, and precise camera language.",
    ),
    KnowledgeEntry(
        id="motion.short_form",
        tags=["short-form", "motion", "pacing"],
        title="Short Form Motion",
        content="Open with immediate movement, vary shot scale every 4-6 seconds, and keep transitions legible.",
    ),
    KnowledgeEntry(
        id="audio.immersive",
        tags=["audio", "sound-design"],
        title="Immersive Audio Cues",
        content="Pair each visual beat with one bed, one transient accent, and scene-specific ambience.",
    ),
    KnowledgeEntry(
        id="prompt.adapter",
        tags=["prompt", "video-model"],
        title="Video Prompt Adapter",
        content="Prompts should name subject, action, environment, camera, lighting, style, and constraints.",
    ),
]


class KnowledgeBase:
    def __init__(self, path: Path | None = None):
        self.path = path or get_settings().knowledge_base_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULT_KNOWLEDGE)

    def load(self) -> list[KnowledgeEntry]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [KnowledgeEntry.model_validate(item) for item in data]

    def save(self, entries: Iterable[KnowledgeEntry]) -> None:
        payload = [entry.model_dump(mode="json") for entry in entries]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def search(self, query: str, tags: list[str] | None = None, limit: int = 4) -> list[KnowledgeEntry]:
        query_terms = {term.lower() for term in query.replace(",", " ").split() if term}
        tag_filter = {tag.lower() for tag in tags or []}
        scored: list[tuple[int, KnowledgeEntry]] = []
        for entry in self.load():
            haystack = " ".join([entry.id, entry.title, entry.content, *entry.tags]).lower()
            score = sum(1 for term in query_terms if term in haystack)
            score += sum(2 for tag in tag_filter if tag in [item.lower() for item in entry.tags])
            if score:
                scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:limit]] or self.load()[:limit]
