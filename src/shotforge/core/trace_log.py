from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Any, Iterator

from shotforge.core.project_state import ProjectState, TraceEvent


class TraceLog:
    def __init__(self, state: ProjectState):
        self.state = state

    def add(self, step: str, status: str, **metadata: Any) -> None:
        self.state.trace_logs.append(TraceEvent(step=step, status=status, metadata=metadata))
        self.state.touch()

    @contextmanager
    def span(self, step: str, **metadata: Any) -> Iterator[None]:
        started = perf_counter()
        self.add(step, "started", **metadata)
        try:
            yield
        except Exception as exc:
            duration_ms = (perf_counter() - started) * 1000
            self.state.trace_logs.append(
                TraceEvent(
                    step=step,
                    status="failed",
                    duration_ms=duration_ms,
                    metadata={**metadata, "error": str(exc)},
                )
            )
            self.state.touch()
            raise
        duration_ms = (perf_counter() - started) * 1000
        self.state.trace_logs.append(
            TraceEvent(step=step, status="completed", duration_ms=duration_ms, metadata=metadata)
        )
        self.state.touch()

__all__ = ["TraceLog"]
