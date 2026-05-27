from __future__ import annotations

from pydantic import BaseModel, Field


class SandboxPolicy(BaseModel):
    sandbox_id: str = "local_dry_run"
    dry_run: bool = True
    allow_file_read: bool = True
    allow_file_write: bool = False
    allow_network: bool = False
    max_runtime_ms: int = 10000
    allowed_paths: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


__all__ = ["SandboxPolicy"]
