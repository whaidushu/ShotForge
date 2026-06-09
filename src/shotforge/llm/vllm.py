from __future__ import annotations

from shotforge.llm.ollama import OllamaProvider
from shotforge.llm.provider import LLMCostMode


class VLLMProvider(OllamaProvider):
    model_name = "vllm"
    cost_mode = LLMCostMode.LOCAL

    def __init__(
        self,
        model: str = "",
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "local",
        temperature: float = 0.2,
        timeout_seconds: float = 60.0,
    ):
        super().__init__(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )

    @property
    def display_name(self) -> str:
        return f"vLLM ({self.model})"
