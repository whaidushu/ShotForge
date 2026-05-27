from __future__ import annotations

from shotforge.llm.ollama import OllamaProvider
from shotforge.llm.provider import LLMCostMode


class VLLMProvider(OllamaProvider):
    model_name = "vllm"
    cost_mode = LLMCostMode.LOCAL

    def __init__(
        self,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        base_url: str = "http://localhost:8000/v1",
    ):
        super().__init__(model=model, base_url=base_url)

    @property
    def display_name(self) -> str:
        return f"vLLM ({self.model})"
