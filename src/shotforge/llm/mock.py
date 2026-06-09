from __future__ import annotations

import hashlib

from shotforge.llm.provider import LLMCostMode


class MockLLMProvider:
    model_name = "mock"
    display_name = "Test LLM"
    cost_mode = LLMCostMode.MOCK

    def complete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        digest = hashlib.sha1(f"{system}:{purpose}:{prompt}".encode("utf-8")).hexdigest()[:8]
        return f"[mock:{purpose}:{digest}] {prompt[:180]}"

    async def acomplete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        return self.complete(prompt, system=system, purpose=purpose)

    async def stream(self, prompt: str, *, system: str = "", purpose: str = ""):
        yield self.complete(prompt, system=system, purpose=purpose)
