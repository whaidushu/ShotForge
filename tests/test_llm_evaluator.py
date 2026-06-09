from __future__ import annotations

import json

from shotforge.core.rubrics import RubricRegistry
from shotforge.evaluators import EvaluatorContext, LLMStoryPromptEvaluator
from shotforge.generators.mock_generator import MockGenerator
from shotforge.llm.registry import build_default_llm_registry
from shotforge.llm.provider import LLMCostMode
from shotforge.workflows.design_workflow import run_design_pipeline


class FakeJudgeLLM:
    model_name = "fake-judge"
    cost_mode = LLMCostMode.MOCK

    def complete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        assert purpose == "story_prompt_evaluation"
        assert "prompt_executability" in prompt
        return json.dumps(
            {
                "signals": [
                    {
                        "shot_id": "shot_01",
                        "dimension_id": "prompt_executability",
                        "score": 0.61,
                        "evidence": ["Prompt lacks a concrete success beat."],
                        "confidence": 0.82,
                    },
                    {
                        "shot_id": "shot_01",
                        "dimension_id": "action_clarity",
                        "score": 0.58,
                        "evidence": ["Action sequence is underspecified."],
                        "confidence": 0.8,
                    },
                ]
            }
        )

    async def acomplete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        return self.complete(prompt, system=system, purpose=purpose)

    async def stream(self, prompt: str, *, system: str = "", purpose: str = ""):
        yield self.complete(prompt, system=system, purpose=purpose)


class BadJudgeLLM(FakeJudgeLLM):
    model_name = "bad-judge"

    def complete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        return "I cannot provide the requested JSON right now."


class RepairingJudgeLLM(FakeJudgeLLM):
    model_name = "repairing-judge"

    def complete(self, prompt: str, *, system: str = "", purpose: str = "") -> str:
        if purpose == "story_prompt_evaluation_repair":
            return json.dumps(
                {
                    "signals": [
                        {
                            "shot_id": "shot_01",
                            "dimension_id": "prompt_executability",
                            "score": 0.64,
                            "evidence": ["Repaired into strict JSON."],
                            "confidence": 0.7,
                        }
                    ]
                }
            )
        return "Here is my evaluation, but not in JSON."


def test_llm_story_prompt_evaluator_returns_structured_signals(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A quiet revenge reveal in a luxury elevator",
        duration_seconds=24,
        language="en",
    )
    generated = MockGenerator().generate(state)
    rubric = RubricRegistry().load("baseline_v1")
    context = EvaluatorContext(state=state, generated_result=generated, rubric=rubric)

    signals = LLMStoryPromptEvaluator(provider=FakeJudgeLLM()).evaluate(context)

    assert {signal.source for signal in signals} == {"llm_story_prompt"}
    assert {signal.dimension_id for signal in signals} == {
        "prompt_executability",
        "action_clarity",
    }
    assert signals[0].shot_id == "shot_01"
    assert signals[0].score == 0.61
    assert signals[0].metadata["provider"] == "fake-judge"


def test_llm_story_prompt_evaluator_repairs_non_json_response(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A precise product reveal",
        duration_seconds=24,
        language="en",
    )
    generated = MockGenerator().generate(state)
    rubric = RubricRegistry().load("baseline_v1")
    context = EvaluatorContext(state=state, generated_result=generated, rubric=rubric)

    signals = LLMStoryPromptEvaluator(provider=RepairingJudgeLLM()).evaluate(context)

    assert signals
    assert signals[0].score == 0.64
    assert signals[0].metadata["provider"] == "repairing-judge"
    get_settings.cache_clear()


def test_llm_story_prompt_evaluator_falls_back_when_json_repair_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A precise product reveal",
        duration_seconds=24,
        language="en",
    )
    generated = MockGenerator().generate(state)
    rubric = RubricRegistry().load("baseline_v1")
    context = EvaluatorContext(state=state, generated_result=generated, rubric=rubric)

    signals = LLMStoryPromptEvaluator(provider=BadJudgeLLM()).evaluate(context)

    assert signals
    assert {signal.score for signal in signals} == {0.5}
    assert {signal.confidence for signal in signals} == {0.2}
    assert signals[0].metadata["provider"] == "bad-judge"
    assert "parse_error" in signals[0].metadata
    get_settings.cache_clear()


def test_llm_evaluator_accepts_raw_signal_array():
    evaluator = LLMStoryPromptEvaluator(provider=FakeJudgeLLM())

    payload = evaluator._parse_json(
        """
        ```json
        [
          {
            "shot_id": "shot_01",
            "dimension_id": "prompt_executability",
            "score": 0.61,
            "evidence": ["Prompt lacks a concrete success beat."]
          }
        ]
        ```
        """
    )

    assert isinstance(payload["signals"], list)
    assert payload["signals"][0]["shot_id"] == "shot_01"


def test_llm_evaluator_flattens_nested_signal_array():
    evaluator = LLMStoryPromptEvaluator(provider=FakeJudgeLLM())

    flattened = evaluator._flatten_signal_items(
        [
            {
                "signals": [
                    {
                        "shot_id": "shot_01",
                        "dimension_id": "prompt_executability",
                        "score": 0.61,
                    }
                ]
            }
        ]
    )

    assert flattened == [
        {
            "shot_id": "shot_01",
            "dimension_id": "prompt_executability",
            "score": 0.61,
        }
    ]


def test_local_ollama_provider_uses_env_configuration(monkeypatch):
    monkeypatch.setenv("SHOTFORGE_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("SHOTFORGE_LLM_MODEL", "local-chat-model")
    monkeypatch.setenv("SHOTFORGE_LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("SHOTFORGE_LLM_TEMPERATURE", "0.1")

    from shotforge.config import get_settings

    get_settings.cache_clear()
    registry = build_default_llm_registry()
    provider = registry.get("ollama")

    assert registry.is_available("ollama")
    assert provider.model == "local-chat-model"
    assert provider.base_url == "http://localhost:11434/v1"
    assert provider.temperature == 0.1


def test_local_vllm_provider_uses_env_configuration(monkeypatch):
    monkeypatch.setenv("SHOTFORGE_LLM_PROVIDER", "vllm")
    monkeypatch.setenv("SHOTFORGE_LLM_MODEL", "local-vllm-model")
    monkeypatch.setenv("SHOTFORGE_LLM_BASE_URL", "http://localhost:8000/v1")
    monkeypatch.setenv("SHOTFORGE_LLM_API_KEY", "local")

    from shotforge.config import get_settings

    get_settings.cache_clear()
    registry = build_default_llm_registry()
    provider = registry.get("vllm")

    assert registry.is_available("vllm")
    assert provider.model == "local-vllm-model"
    assert provider.base_url == "http://localhost:8000/v1"
    assert provider.api_key == "local"
