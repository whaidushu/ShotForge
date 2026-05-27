from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    call_id: str = Field(default_factory=lambda: f"tool_{uuid4().hex[:12]}")
    tool_name: str
    status: Literal["started", "completed", "failed"]
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float | None = None
    input_preview: dict[str, Any] = Field(default_factory=dict)
    output_preview: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["ToolCallRecord"]
