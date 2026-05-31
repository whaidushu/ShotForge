from __future__ import annotations

from shotforge.llm.provider import LLMCostMode


class OllamaProvider:
    model_name = "ollama"
    cost_mode = LLMCostMode.FREE

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        temperature: float = 0.2,
        timeout_seconds: float = 60.0,
    ):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key or "ollama"
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds

    @property
    def display_name(self) -> str:
        return f"Ollama ({self.model})"

    def complete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        from openai import OpenAI

        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout_seconds,
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),
            temperature=self.temperature,
            **self._response_format_kwargs(purpose),
        )
        return response.choices[0].message.content or ""

    async def acomplete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout_seconds,
        )
        response = await client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),
            temperature=self.temperature,
            **self._response_format_kwargs(purpose),
        )
        return response.choices[0].message.content or ""

    async def stream(self, prompt: str, *, system: str = "", purpose: str = ""):
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout_seconds,
        )
        stream = await client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),
            temperature=self.temperature,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _messages(self, prompt: str, system: str) -> list[dict[str, str]]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _response_format_kwargs(self, purpose: str) -> dict[str, object]:
        if purpose.startswith("story_prompt_evaluation"):
            return {"response_format": {"type": "json_object"}}
        return {}
