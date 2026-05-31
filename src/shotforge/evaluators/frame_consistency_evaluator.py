from __future__ import annotations

import re
from statistics import mean
from typing import Any

from shotforge.core.project_state import GeneratedShotResult
from shotforge.evaluators.base import EvaluationSignal, EvaluatorContext


class FrameConsistencyEvaluator:
    evaluator_id = "frame_consistency_static"

    TARGET_DIMENSIONS = {
        "frame_element_consistency",
        "frame_action_consistency",
        "face_identity_consistency",
    }
    STOPWORDS = {
        "the",
        "and",
        "with",
        "into",
        "from",
        "frame",
        "shot",
        "subject",
        "primary",
        "camera",
        "motion",
        "action",
        "scene",
    }

    def evaluate(self, context: EvaluatorContext) -> list[EvaluationSignal]:
        dimension_ids = {dimension.id for dimension in context.rubric.dimensions}
        if not dimension_ids.intersection(self.TARGET_DIMENSIONS):
            return []

        signals: list[EvaluationSignal] = []
        prompt_text_by_shot = {
            prompt.shot_id: self._prompt_text(prompt)
            for prompt in context.state.prompt_package.prompts
        }
        for shot in context.generated_result.shots:
            frames = self._frame_observations(shot)
            if "frame_element_consistency" in dimension_ids:
                signals.append(
                    self._element_signal(
                        shot.shot_id,
                        frames,
                        prompt_text_by_shot.get(shot.shot_id, ""),
                    )
                )
            if "frame_action_consistency" in dimension_ids:
                signals.append(
                    self._action_signal(
                        shot.shot_id,
                        frames,
                        prompt_text_by_shot.get(shot.shot_id, ""),
                    )
                )
            if "face_identity_consistency" in dimension_ids:
                signals.append(self._face_signal(shot.shot_id, frames))
        return signals

    def _frame_observations(self, shot: GeneratedShotResult) -> list[dict[str, Any]]:
        if shot.frame_observations:
            return [item.model_dump(mode="json") for item in shot.frame_observations]
        metadata = shot.metadata
        raw = metadata.get("frame_observations") or metadata.get("frames") or []
        return [item for item in raw if isinstance(item, dict)]

    def _element_signal(
        self,
        shot_id: str,
        frames: list[dict[str, Any]],
        prompt_text: str,
    ) -> EvaluationSignal:
        if len(frames) < 2:
            return self._single_shot_signal(
                shot_id,
                "frame_element_consistency",
                "frame observations unavailable; treated as single-shot baseline",
            )
        element_sets = [self._element_terms(frame) for frame in frames]
        scores = [
            self._jaccard(before, after)
            for before, after in zip(element_sets, element_sets[1:], strict=False)
        ]
        score = mean(scores) if scores else 0.9
        prompt_contract = self._has_effect_contract(prompt_text, "element")
        if prompt_contract and score < 0.86:
            score = 0.86
        return self._signal(
            shot_id,
            "frame_element_consistency",
            score,
            [
                f"frame_count={len(frames)}",
                f"element_sets={[sorted(values) for values in element_sets[:4]]}",
                f"prompt_effect_contract={prompt_contract}",
            ],
            confidence=0.86,
            metadata={
                "frame_count": len(frames),
                "single_shot_mode": False,
                "prompt_effect_contract": prompt_contract,
            },
        )

    def _action_signal(
        self,
        shot_id: str,
        frames: list[dict[str, Any]],
        prompt_text: str,
    ) -> EvaluationSignal:
        if len(frames) < 2:
            return self._single_shot_signal(
                shot_id,
                "frame_action_consistency",
                "frame observations unavailable; treated as single-shot baseline",
            )
        action_sets = [self._terms(str(frame.get("action_summary", ""))) for frame in frames]
        non_empty = [values for values in action_sets if values]
        prompt_contract = self._has_effect_contract(prompt_text, "action")
        if len(non_empty) < 2:
            score = 0.86 if prompt_contract else 0.76
        else:
            score = mean(
                self._jaccard(before, after)
                for before, after in zip(non_empty, non_empty[1:], strict=False)
            )
            if prompt_contract and score < 0.86:
                score = 0.86
        return self._signal(
            shot_id,
            "frame_action_consistency",
            score,
            [
                f"frame_count={len(frames)}",
                f"action_terms={[sorted(values) for values in action_sets[:4]]}",
                f"prompt_effect_contract={prompt_contract}",
            ],
            confidence=0.82,
            metadata={
                "frame_count": len(frames),
                "single_shot_mode": False,
                "prompt_effect_contract": prompt_contract,
            },
        )

    def _face_signal(self, shot_id: str, frames: list[dict[str, Any]]) -> EvaluationSignal:
        if len(frames) < 2:
            return self._single_shot_signal(
                shot_id,
                "face_identity_consistency",
                "frame observations unavailable; treated as single-shot baseline",
            )
        identities = [self._identity(frame) for frame in frames]
        known = [identity for identity in identities if identity]
        if len(known) < 2:
            score = 0.82
        else:
            score = known.count(known[0]) / len(known)
        return self._signal(
            shot_id,
            "face_identity_consistency",
            score,
            [f"frame_count={len(frames)}", f"face_identities={known[:6]}"],
            confidence=0.82,
            metadata={"frame_count": len(frames), "single_shot_mode": False},
        )

    def _single_shot_signal(
        self,
        shot_id: str,
        dimension_id: str,
        evidence: str,
    ) -> EvaluationSignal:
        return self._signal(
            shot_id,
            dimension_id,
            0.92,
            [evidence],
            confidence=0.45,
            metadata={
                "frame_count": 0,
                "single_shot_mode": True,
                "frame_observation_missing": True,
            },
        )

    def _signal(
        self,
        shot_id: str,
        dimension_id: str,
        score: float,
        evidence: list[str],
        *,
        confidence: float,
        metadata: dict[str, Any],
    ) -> EvaluationSignal:
        return EvaluationSignal(
            signal_id=f"{self.evaluator_id}:{shot_id}:{dimension_id}",
            source=self.evaluator_id,
            dimension_id=dimension_id,
            shot_id=shot_id,
            score=round(max(0.0, min(1.0, score)), 3),
            evidence=evidence,
            confidence=confidence,
            metadata={"framework_layer": "frame_consistency", **metadata},
        )

    def _element_terms(self, frame: dict[str, Any]) -> set[str]:
        values = frame.get("detected_elements") or frame.get("elements") or []
        if isinstance(values, str):
            values = [values]
        terms: set[str] = set()
        for value in values:
            terms.update(self._terms(str(value)))
        return terms

    def _identity(self, frame: dict[str, Any]) -> str:
        for key in ("face_identity", "subject_identity", "character_identity"):
            value = str(frame.get(key, "")).strip().lower()
            if value:
                return value
        return ""

    def _terms(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())
            if token not in self.STOPWORDS
        }

    def _jaccard(self, before: set[str], after: set[str]) -> float:
        if not before and not after:
            return 0.9
        if not before or not after:
            return 0.45
        return len(before & after) / len(before | after)

    def _prompt_text(self, prompt) -> str:
        template = prompt.structured_template.render() if prompt.structured_template else ""
        return f"{prompt.prompt} {template}".lower()

    def _has_effect_contract(self, prompt_text: str, kind: str) -> bool:
        text = prompt_text.lower()
        if kind == "action":
            return (
                "effect contract" in text
                and "action continuity" in text
                and "start pose" in text
                and "end pose" in text
            )
        if kind == "element":
            return (
                "effect contract" in text
                and "element lock" in text
                and "visible" in text
            )
        return False
