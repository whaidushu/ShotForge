from __future__ import annotations

from collections.abc import AsyncIterator

from shotforge.config import Settings, get_settings
from shotforge.llm.provider import LLMCostMode


class OpenAICompatibleProvider:
    model_name = "openai-compatible"
    display_name = "OpenAI-compatible LLM"
    cost_mode = LLMCostMode.PAID

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float | None = None,
        timeout_seconds: float | None = None,
        settings: Settings | None = None,
    ):
        settings = settings or get_settings()
        self.model = model or settings.llm_model
        self.base_url = base_url if base_url is not None else settings.llm_base_url
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.llm_timeout_seconds
        )

    def is_configured(self) -> bool:
        return bool(self.model and self.api_key)

    def complete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        from openai import OpenAI

        self._ensure_configured()
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url or None,
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

        self._ensure_configured()
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url or None,
            timeout=self.timeout_seconds,
        )
        response = await client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),
            temperature=self.temperature,
            **self._response_format_kwargs(purpose),
        )
        return response.choices[0].message.content or ""

    async def stream(
        self,
        prompt: str,
        *,
        system: str = "",
        purpose: str = "",
    ) -> AsyncIterator[str]:
        from openai import AsyncOpenAI

        self._ensure_configured()
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url or None,
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

    def _ensure_configured(self) -> None:
        if not self.model:
            raise RuntimeError("SHOTFORGE_LLM_MODEL is required for openai-compatible LLM.")
        if not self.api_key:
            raise RuntimeError("SHOTFORGE_LLM_API_KEY is required for openai-compatible LLM.")
