from __future__ import annotations

from typing import Protocol


class SandboxRunner(Protocol):
    def run(self, command: list[str], timeout_seconds: int = 60) -> str:
        """Run an isolated command and return captured output."""
