from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from shotforge.core.physical_targets import required_element_labels
from shotforge.core.project_state import GeneratedShotResult, PromptItem, ProjectState, ShotSpec
from shotforge.evaluators.base import EvaluationSignal, EvaluatorContext


@dataclass(frozen=True)
class PhysicalConstraintSet:
    expected_subject_count: int | None
    expected_colors: list[str]
    expected_elements: list[str]
    prompt_text: str
    observed_text: str
    observation_mode: str


class PhysicalEffectEvaluator:
    evaluator_id = "physical_effect_static"

    COLOR_TERMS = {
        "black": ("black", "dark", "noir", "黑", "黑色"),
        "white": ("white", "ivory", "白", "白色"),
        "red": ("red", "crimson", "scarlet", "红", "红色"),
        "blue": ("blue", "cyan", "azure", "蓝", "蓝色"),
        "green": ("green", "emerald", "绿色", "绿"),
        "yellow": ("yellow", "amber", "黄色", "黄"),
        "gold": ("gold", "golden", "金色", "金"),
        "silver": ("silver", "metallic", "银色", "银"),
        "purple": ("purple", "violet", "紫色", "紫"),
        "pink": ("pink", "magenta", "粉色", "粉"),
        "orange": ("orange", "橙色", "橙"),
        "neon": ("neon", "glowing", "luminous", "霓虹", "发光"),
    }
    NUMBER_WORDS = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "一": 1,
        "一个": 1,
        "一只": 1,
        "一位": 1,
        "两": 2,
        "两个": 2,
        "两只": 2,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    COUNT_TARGETS = (
        "subject",
        "subjects",
        "character",
        "characters",
        "person",
        "people",
        "robot",
        "robots",
        "cat",
        "cats",
        "dog",
        "dogs",
        "protagonist",
        "protagonists",
        "actor",
        "actors",
    )
    STOPWORDS = {
        "with",
        "from",
        "into",
        "that",
        "this",
        "then",
        "shot",
        "scene",
        "style",
        "visual",
        "camera",
        "clear",
        "primary",
        "subject",
        "subjects",
        "character",
        "characters",
        "cinematic",
        "required",
        "visible",
        "elements",
        "audio",
        "motion",
        "exact",
        "requested",
    }

    def evaluate(self, context: EvaluatorContext) -> list[EvaluationSignal]:
        dimension_ids = {dimension.id for dimension in context.rubric.dimensions}
        target_dimensions = {
            "subject_count",
            "color_alignment",
            "element_presence",
            "element_description",
        }
        if not dimension_ids.intersection(target_dimensions):
            return []

        signals: list[EvaluationSignal] = []
        for shot in context.state.shots:
            generated_shot = next(
                (item for item in context.generated_result.shots if item.shot_id == shot.shot_id),
                None,
            )
            prompt = next(
                (item for item in context.state.prompt_package.prompts if item.shot_id == shot.shot_id),
                None,
            )
            constraints = self._constraints(context.state, shot, generated_shot, prompt)
            if "subject_count" in dimension_ids:
                signals.append(self._subject_count_signal(shot.shot_id, constraints))
            if "color_alignment" in dimension_ids:
                signals.append(self._color_signal(shot.shot_id, constraints))
            if "element_presence" in dimension_ids:
                signals.append(self._element_presence_signal(shot.shot_id, constraints))
            if "element_description" in dimension_ids:
                signals.append(self._element_description_signal(shot.shot_id, constraints, prompt))
        return signals

    def _constraints(
        self,
        state: ProjectState,
        shot: ShotSpec,
        generated_shot: GeneratedShotResult | None,
        prompt: PromptItem | None,
    ) -> PhysicalConstraintSet:
        prompt_text = self._prompt_text(prompt)
        expected_text = " ".join(
            [
                state.user_idea,
                shot.title,
                shot.description,
                " ".join(shot.key_visuals),
                prompt_text,
            ]
        )
        observed_text, observation_mode = self._observed_text(generated_shot)
        return PhysicalConstraintSet(
            expected_subject_count=self._expected_subject_count(state, expected_text),
            expected_colors=self._extract_colors(expected_text),
            expected_elements=self._expected_elements(state, shot, prompt),
            prompt_text=prompt_text.lower(),
            observed_text=observed_text.lower(),
            observation_mode=observation_mode,
        )

    def _subject_count_signal(
        self,
        shot_id: str,
        constraints: PhysicalConstraintSet,
    ) -> EvaluationSignal:
        expected = constraints.expected_subject_count
        observed = self._extract_subject_count(constraints.observed_text)
        prompt_count = self._extract_subject_count(constraints.prompt_text)
        if expected is None:
            score = 0.95
            evidence = ["no explicit subject-count target found"]
        elif observed == expected:
            score = 0.96
            evidence = [f"expected_count={expected}", f"observed_count={observed}"]
        elif constraints.observation_mode == "real_video_unobserved":
            score = 0.52
            evidence = [
                f"expected_count={expected}",
                "real video has no visual detection result",
                f"prompt_count={prompt_count}",
            ]
        elif observed is None and prompt_count == expected:
            score = 0.82
            evidence = [
                f"expected_count={expected}",
                "visual observation has no count",
                f"prompt_count={prompt_count}",
            ]
        else:
            score = 0.42 if observed is not None else 0.58
            evidence = [f"expected_count={expected}", f"observed_count={observed}"]
        return self._signal("subject_count", shot_id, score, evidence, constraints)

    def _color_signal(self, shot_id: str, constraints: PhysicalConstraintSet) -> EvaluationSignal:
        expected = constraints.expected_colors
        observed = self._extract_colors(constraints.observed_text)
        prompt_colors = self._extract_colors(constraints.prompt_text)
        if not expected:
            score = 0.95
            evidence = ["no explicit color target found"]
        else:
            missing_observed = [color for color in expected if color not in observed]
            missing_prompt = [color for color in expected if color not in prompt_colors]
            if not missing_observed:
                score = 0.95
            elif constraints.observation_mode == "real_video_unobserved":
                score = 0.52
            elif not missing_prompt:
                score = 0.88 if self._has_color_lock_contract(constraints.prompt_text) else 0.8
            else:
                score = max(0.35, 1 - 0.18 * len(missing_prompt) - 0.1 * len(missing_observed))
            evidence = [
                f"expected_colors={expected}",
                f"observed_colors={observed}",
                f"missing_from_prompt={missing_prompt}",
                f"missing_from_observation={missing_observed}",
                f"prompt_effect_contract={self._has_color_lock_contract(constraints.prompt_text)}",
            ]
        return self._signal("color_alignment", shot_id, score, evidence, constraints)

    def _element_presence_signal(
        self,
        shot_id: str,
        constraints: PhysicalConstraintSet,
    ) -> EvaluationSignal:
        expected = constraints.expected_elements
        if not expected:
            score = 0.9
            evidence = ["no concrete element targets found"]
        else:
            observed_hits = self._hits(expected, constraints.observed_text)
            prompt_hits = self._hits(expected, constraints.prompt_text)
            if constraints.observation_mode == "real_video_unobserved":
                coverage = len(prompt_hits) / len(expected)
                score = 0.45 + 0.12 * coverage
            elif constraints.observation_mode != "visual_observation":
                coverage = len(prompt_hits) / len(expected)
                score = 0.88 if coverage >= 0.5 else 0.72 + 0.2 * coverage
            elif observed_hits:
                score = len(observed_hits) / len(expected)
            else:
                score = 0.82 if len(prompt_hits) == len(expected) else 0.58 + 0.2 * (
                    len(prompt_hits) / len(expected)
                )
            missing_elements = [term for term in expected if term not in observed_hits]
            evidence = [
                f"expected_elements={expected}",
                f"observed_hits={observed_hits}",
                f"prompt_hits={prompt_hits}",
                f"missing_elements={missing_elements}",
            ]
        return self._signal("element_presence", shot_id, min(1.0, score), evidence, constraints)

    def _element_description_signal(
        self,
        shot_id: str,
        constraints: PhysicalConstraintSet,
        prompt: PromptItem | None,
    ) -> EvaluationSignal:
        template = prompt.structured_template if prompt else None
        if template is None:
            return self._signal(
                "element_description",
                shot_id,
                0.45,
                ["structured prompt template missing"],
                constraints,
            )
        fields = {
            "character_identity": template.character_identity,
            "scene_constraints": template.scene_constraints,
            "physical_constraints": "; ".join(template.physical_constraints),
            "action_sequence": template.action_sequence,
            "success_criteria": "; ".join(template.success_criteria),
        }
        present = [key for key, value in fields.items() if str(value).strip()]
        score = 0.5 + 0.1 * len(present)
        if constraints.expected_colors:
            score += 0.05 if self._extract_colors(template.render()) else -0.05
        if constraints.expected_subject_count is not None:
            score += 0.05 if self._extract_subject_count(template.render()) else -0.08
        evidence = [f"present_fields={present}", f"expected_elements={constraints.expected_elements}"]
        return self._signal("element_description", shot_id, max(0.0, min(1.0, score)), evidence, constraints)

    def _signal(
        self,
        dimension_id: str,
        shot_id: str,
        score: float,
        evidence: list[str],
        constraints: PhysicalConstraintSet,
    ) -> EvaluationSignal:
        return EvaluationSignal(
            signal_id=f"{self.evaluator_id}:{shot_id}:{dimension_id}",
            source=self.evaluator_id,
            dimension_id=dimension_id,
            shot_id=shot_id,
            score=round(score, 3),
            evidence=[*evidence, f"observation_mode={constraints.observation_mode}"],
            confidence=0.9 if constraints.observation_mode == "visual_observation" else 0.55,
            metadata={
                "expected_subject_count": constraints.expected_subject_count,
                "expected_colors": constraints.expected_colors,
                "expected_elements": constraints.expected_elements,
                "missing_elements": self._missing_elements(constraints),
                "observation_mode": constraints.observation_mode,
                "visual_observation_missing": constraints.observation_mode != "visual_observation",
                "framework_layer": "style_color" if dimension_id == "color_alignment" else "physical_effect",
            },
        )

    def _prompt_text(self, prompt: PromptItem | None) -> str:
        if prompt is None:
            return ""
        template_text = prompt.structured_template.render() if prompt.structured_template else ""
        return f"{prompt.prompt} {template_text}"

    def _observed_text(self, generated_shot: GeneratedShotResult | None) -> tuple[str, str]:
        if generated_shot is None:
            return "", "missing_generation"
        text_parts = [generated_shot.observed_summary, *generated_shot.detected_elements]
        is_mock = (
            generated_shot.metadata.get("generator_mode") == "deterministic_mock"
            or generated_shot.mock_video_uri.startswith("mock://")
        )
        if generated_shot.detected_elements and not is_mock:
            mode = "visual_observation"
        elif not is_mock:
            mode = "real_video_unobserved"
        else:
            mode = "prompt_proxy"
        return " ".join(part for part in text_parts if part), mode

    def _expected_subject_count(self, state: ProjectState, expected_text: str) -> int | None:
        targets = state.metadata.get("physical_targets", {}).get("targets", [])
        if isinstance(targets, list):
            for target in targets:
                if isinstance(target, dict) and target.get("type") == "subject":
                    count = target.get("count")
                    if isinstance(count, int):
                        return count
        return self._extract_subject_count(expected_text)

    def _extract_subject_count(self, text: str) -> int | None:
        normalized = text.lower()
        target_pattern = "|".join(self.COUNT_TARGETS)
        patterns = [
            rf"\bexactly\s+(\d+|{'|'.join(self.NUMBER_WORDS)})\s+"
            rf"(?:primary\s+)?(?:[a-z-]+\s+){{0,3}}(?:{target_pattern})\b",
            rf"\b(\d+|{'|'.join(self.NUMBER_WORDS)})\s+"
            rf"(?:primary\s+)?(?:[a-z-]+\s+){{0,3}}(?:{target_pattern})\b",
            r"([一二两三四五六七八九十])\s*(?:个|只|位|名)\s*(?:主体|角色|人物|人|猫|狗|机器人)",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return self._number_value(match.group(1))
        return None

    def _number_value(self, value: str) -> int | None:
        if value.isdigit():
            return int(value)
        return self.NUMBER_WORDS.get(value)

    def _extract_colors(self, text: str) -> list[str]:
        lowered = text.lower()
        colors = []
        for color, aliases in self.COLOR_TERMS.items():
            if any(self._contains_color_alias(lowered, alias) for alias in aliases):
                colors.append(color)
        return colors

    def _contains_color_alias(self, lowered: str, alias: str) -> bool:
        if re.fullmatch(r"[a-z-]+", alias):
            return re.search(rf"\b{re.escape(alias)}\b", lowered) is not None
        return alias in lowered

    def _expected_elements(
        self,
        state: ProjectState,
        shot: ShotSpec,
        prompt: PromptItem | None,
    ) -> list[str]:
        physical_targets = required_element_labels(state.metadata.get("physical_targets"))
        if physical_targets:
            return physical_targets[:10]
        values = [shot.title, *shot.key_visuals]
        if prompt and prompt.structured_template:
            values.extend(
                [
                    prompt.structured_template.character_identity,
                    prompt.structured_template.scene_constraints,
                    prompt.structured_template.action_sequence,
                ]
            )
        return self._extract_element_terms(values)[:8]

    def _extract_element_terms(self, values: Iterable[str]) -> list[str]:
        terms: list[str] = []
        for value in values:
            lowered = value.lower()
            if re.search(r"[\u4e00-\u9fff]", lowered):
                candidate = re.sub(r"[，。；：、,.!?;:]", " ", lowered).strip()
                if candidate and candidate not in terms:
                    terms.append(candidate)
                continue
            for token in re.findall(r"[a-z][a-z0-9-]{3,}", lowered):
                if token in self.STOPWORDS:
                    continue
                if any(token in aliases for aliases in self.COLOR_TERMS.values()):
                    continue
                if token not in terms:
                    terms.append(token)
        return terms

    def _hits(self, expected: list[str], text: str) -> list[str]:
        return [term for term in expected if term.lower() in text.lower()]

    def _missing_elements(self, constraints: PhysicalConstraintSet) -> list[str]:
        observed_hits = self._hits(constraints.expected_elements, constraints.observed_text)
        return [term for term in constraints.expected_elements if term not in observed_hits]

    def _has_color_lock_contract(self, text: str) -> bool:
        lowered = text.lower()
        return (
            "effect contract" in lowered
            and "color lock" in lowered
            and ("persistent" in lowered or "stable" in lowered)
        )
