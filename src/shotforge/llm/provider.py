from __future__ import annotations

from enum import Enum
from typing import AsyncIterator, Protocol, runtime_checkable


class LLMCostMode(str, Enum):
    MOCK = "mock"
    FREE = "free"
    LOCAL = "local"
    PAID = "paid"


@runtime_checkable
class LLMProvider(Protocol):
    model_name: str
    cost_mode: LLMCostMode

    def complete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        """Return a complete text response."""

    async def acomplete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        """Return a complete text response asynchronously."""

    async def stream(
        self,
        prompt: str,
        *,
        system: str = "",
        purpose: str = "",
    ) -> AsyncIterator[str]:
        """Stream text chunks asynchronously."""
