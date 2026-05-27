from __future__ import annotations

import hashlib


class MockLLM:
    """Deterministic text helper used to prove the harness without external LLM calls."""

    def complete(self, prompt: str, *, purpose: str) -> str:
        digest = hashlib.sha1(f"{purpose}:{prompt}".encode("utf-8")).hexdigest()[:8]
        return f"[mock:{purpose}:{digest}] {prompt[:180]}"
