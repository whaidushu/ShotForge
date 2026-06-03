from __future__ import annotations

import json
import re
from typing import Any
from uuid import uuid4

from shotforge.core.project_state import runtime_language
from shotforge.evaluators.base import EvaluationSignal, EvaluatorContext
from shotforge.llm import LLMProvider, build_default_llm_registry


class LLMStoryPromptEvaluator:
    evaluator_id = "llm_story_prompt"

    def __init__(self, provider: LLMProvider | None = None, provider_name: str | None = None):
        if provider is not None:
            self.provider = provider
        else:
            registry = build_default_llm_registry()
            self.provider = registry.get(provider_name or self._configured_provider_name())

    def evaluate(self, context: EvaluatorContext) -> list[EvaluationSignal]:
        prompt = self._prompt(context)
        response = self.provider.complete(
            prompt,
            system=self._system_prompt(runtime_language(context.state)),
            purpose="story_prompt_evaluation",
        )
        try:
            payload = self._parse_json(response)
        except ValueError as exc:
            payload = self._repair_response(context, prompt, response, exc)
        return self._signals(context, payload)

    def _configured_provider_name(self) -> str:
        from shotforge.config import get_settings

        return get_settings().llm_provider

    def _system_prompt(self, language: str) -> str:
        response_language = "Chinese" if language == "zh" else "English"
        return (
            "You are a strict video creative QA evaluator. "
            "Score only the provided storyboard and prompt package, not imagined final video. "
            f"Write evidence in {response_language}. "
            "Return only valid JSON. Do not include markdown."
        )

    def _prompt(self, context: EvaluatorContext) -> str:
        state = context.state
        dimensions = [
            {
                "dimension_id": dimension.id,
                "label": dimension.label(runtime_language(state)),
                "target": dimension.target,
                "threshold": dimension.issue_rule.threshold,
                "correction_type": dimension.issue_rule.correction_type,
                "prompt_fields": dimension.prompt_fields,
            }
            for dimension in context.rubric.dimensions
        ]
        shots = []
        prompt_by_shot = {item.shot_id: item for item in state.prompt_package.prompts}
        audio_by_shot = {item.shot_id: item for item in state.audio_cues}
        for shot in state.shots:
            prompt_item = prompt_by_shot.get(shot.shot_id)
            audio = audio_by_shot.get(shot.shot_id)
            shots.append(
                {
                    "shot_id": shot.shot_id,
                    "title": shot.title,
                    "duration_seconds": shot.duration_seconds,
                    "description": shot.description,
                    "shot_type": shot.shot_type,
                    "key_visuals": shot.key_visuals,
                    "motion": shot.motion.model_dump(mode="json") if shot.motion else None,
                    "audio": audio.model_dump(mode="json") if audio else None,
                    "prompt": prompt_item.prompt if prompt_item else "",
                    "structured_template": (
                        prompt_item.structured_template.model_dump(mode="json")
                        if prompt_item and prompt_item.structured_template
                        else None
                    ),
                }
            )
        payload = {
            "user_idea": state.user_idea,
            "style": state.style,
            "language": runtime_language(state),
            "rubric_id": context.rubric.id,
            "dimensions": dimensions,
            "shots": shots,
        }
        return (
            "Evaluate the storyboard and prompt package against every dimension for every shot. "
            "Scores must be calibrated between 0 and 1: 0.90 means production-ready, "
            "0.72 means acceptable, 0.50 means clear revision needed. "
            "Return this exact JSON shape:\n"
            '{"signals":[{"shot_id":"shot_1","dimension_id":"prompt_executability",'
            '"score":0.67,"evidence":["specific reason"],"confidence":0.8}]}\n\n'
            f"Input:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def _parse_json(self, response: str) -> dict[str, Any]:
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(?P<json>[\s\S]*?)```", response)
            candidate = match.group("json").strip() if match else response
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                object_match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
                array_match = re.search(r"\[.*\]", candidate, flags=re.DOTALL)
                json_text = object_match.group(0) if object_match else (
                    array_match.group(0) if array_match else ""
                )
                if not json_text:
                    raise ValueError("LLM evaluator returned no JSON object.") from None
                parsed = json.loads(json_text)
        if isinstance(parsed, list):
            return {"signals": parsed}
        if not isinstance(parsed, dict):
            raise ValueError("LLM evaluator response must be a JSON object.")
        return parsed

    def _repair_response(
        self,
        context: EvaluatorContext,
        original_prompt: str,
        response: str,
        error: ValueError,
    ) -> dict[str, Any]:
        repair_prompt = (
            "The previous evaluator response was not valid JSON for this required shape:\n"
            '{"signals":[{"shot_id":"shot_01","dimension_id":"prompt_executability",'
            '"score":0.67,"evidence":["specific reason"],"confidence":0.8}]}\n\n'
            "Return only a corrected JSON object. Do not include markdown or commentary.\n\n"
            f"Parser error: {error}\n\n"
            f"Previous response:\n{response[:4000]}\n\n"
            f"Original evaluation request:\n{original_prompt[:6000]}"
        )
        try:
            repaired = self.provider.complete(
                repair_prompt,
                system=self._system_prompt(runtime_language(context.state)),
                purpose="story_prompt_evaluation_repair",
            )
            return self._parse_json(repaired)
        except Exception as repair_error:
            return self._fallback_payload(context, response, error, repair_error)

    def _fallback_payload(
        self,
        context: EvaluatorContext,
        response: str,
        error: ValueError,
        repair_error: Exception,
    ) -> dict[str, Any]:
        shot_id = context.state.shots[0].shot_id if context.state.shots else None
        signals = []
        for dimension in context.rubric.dimensions:
            signals.append(
                {
                    "shot_id": shot_id,
                    "dimension_id": dimension.id,
                    "score": 0.5,
                    "confidence": 0.2,
                    "evidence": [
                        "LLM evaluator response was not valid JSON; this fallback signal keeps the run exportable.",
                        f"Parser error: {error}",
                    ],
                    "metadata": {
                        "parse_error": str(error),
                        "repair_error": str(repair_error),
                        "raw_response_preview": response[:500],
                    },
                }
            )
        return {"signals": signals}

    def _signals(self, context: EvaluatorContext, payload: dict[str, Any]) -> list[EvaluationSignal]:
        raw_signals = payload.get("signals", [])
        if not isinstance(raw_signals, list):
            raise ValueError("LLM evaluator response field 'signals' must be a list.")
        raw_signals = self._flatten_signal_items(raw_signals)
        valid_shot_ids = {shot.shot_id for shot in context.state.shots}
        valid_dimension_ids = {dimension.id for dimension in context.rubric.dimensions}
        signals: list[EvaluationSignal] = []
        for item in raw_signals:
            if not isinstance(item, dict):
                continue
            shot_id = str(item.get("shot_id", "")).strip()
            dimension_id = str(item.get("dimension_id", "")).strip()
            if shot_id not in valid_shot_ids or dimension_id not in valid_dimension_ids:
                continue
            score = self._score(item.get("score", 0.7))
            evidence = item.get("evidence", [])
            if isinstance(evidence, str):
                evidence = [evidence]
            if not isinstance(evidence, list):
                evidence = []
            signals.append(
                EvaluationSignal(
                    signal_id=f"llm_signal_{uuid4().hex[:12]}",
                    source=self.evaluator_id,
                    dimension_id=dimension_id,
                    score=score,
                    shot_id=shot_id,
                    evidence=[str(value) for value in evidence[:3]],
                    confidence=self._score(item.get("confidence", 0.75)),
                    metadata={
                        "provider": self.provider.model_name,
                        "model": getattr(self.provider, "model", self.provider.model_name),
                        "judge_type": "storyboard_prompt",
                        **item.get("metadata", {}),
                    },
                )
            )
        return signals

    def _flatten_signal_items(self, items: list[Any]) -> list[Any]:
        flattened: list[Any] = []
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("signals"), list):
                flattened.extend(item["signals"])
            else:
                flattened.append(item)
        return flattened

    def _score(self, value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.7
        return max(0.0, min(1.0, round(score, 3)))
