from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any

from pydantic import BaseModel, Field

from shotforge.infra.sandbox.policy import SandboxPolicy


class SandboxResult(BaseModel):
    status: str
    output: Any = None
    latency_ms: float = 0.0
    metadata: dict = Field(default_factory=dict)


class LocalSandbox:
    def __init__(self, policy: SandboxPolicy | None = None):
        self.policy = policy or SandboxPolicy()

    def run(self, task_name: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> SandboxResult:
        if self.policy.dry_run:
            return SandboxResult(
                status="dry_run",
                metadata={"task_name": task_name, "policy": self.policy.model_dump(mode="json")},
            )
        started = perf_counter()
        output = func(*args, **kwargs)
        return SandboxResult(
            status="completed",
            output=output,
            latency_ms=(perf_counter() - started) * 1000,
            metadata={"task_name": task_name},
        )


__all__ = ["LocalSandbox", "SandboxResult"]
