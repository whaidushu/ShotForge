from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Protocol

from shotforge.core.project_state import FrameObservation, GeneratedShotResult, ProjectState


class FrameObserver(Protocol):
    observer_id: str

    def observe(
        self,
        *,
        state: ProjectState,
        generated_shot: GeneratedShotResult,
        frame_paths: list[Path],
    ) -> list[FrameObservation]:
        """Return frame-level observations for one generated shot."""


class HeuristicFrameObserver:
    observer_id = "heuristic_frame_observer"

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
        "required",
        "visible",
        "elements",
        "audio",
        "motion",
        "cinematic",
    }

    def observe(
        self,
        *,
        state: ProjectState,
        generated_shot: GeneratedShotResult,
        frame_paths: list[Path],
    ) -> list[FrameObservation]:
        shot = next((item for item in state.shots if item.shot_id == generated_shot.shot_id), None)
        prompt = next(
            (item for item in state.prompt_package.prompts if item.shot_id == generated_shot.shot_id),
            None,
        )
        text = " ".join(
            [
                state.user_idea,
                shot.title if shot else "",
                shot.description if shot else "",
                " ".join(shot.key_visuals) if shot else "",
                prompt.prompt if prompt else "",
                prompt.structured_template.render() if prompt and prompt.structured_template else "",
            ]
        )
        elements = self._elements(text)
        action = self._action_summary(shot, prompt)
        identity = self._identity(state)
        paths = frame_paths or []
        frame_count = len(paths) if paths else 3
        observations = []
        for index in range(frame_count):
            observations.append(
                FrameObservation(
                    frame_index=index,
                    timestamp_seconds=float(index) if paths else None,
                    frame_path=str(paths[index]) if paths else "",
                    detected_elements=elements,
                    face_identity=identity,
                    action_summary=action,
                    source=self.observer_id,
                    confidence=0.5 if paths else 0.35,
                    metadata={
                        "observation_mode": "extracted_frame_heuristic" if paths else "prompt_proxy",
                        "shot_id": generated_shot.shot_id,
                    },
                )
            )
        return observations

    def _elements(self, text: str) -> list[str]:
        lowered = text.lower()
        terms = []
        for token in re.findall(r"[a-z][a-z0-9-]{3,}", lowered):
            if token in self.STOPWORDS or token in terms:
                continue
            terms.append(token)
        if re.search(r"[\u4e00-\u9fff]", text):
            chunks = [
                chunk.strip()
                for chunk in re.split(r"[，。；：、?.!?;:\s]+", text)
                if len(chunk.strip()) >= 2
            ]
            terms.extend(chunk for chunk in chunks[:5] if chunk not in terms)
        return terms[:8]

    def _action_summary(self, shot, prompt) -> str:
        if shot and shot.motion:
            return shot.motion.subject_motion
        if shot:
            return shot.description
        return prompt.prompt[:160] if prompt else ""

    def _identity(self, state: ProjectState) -> str:
        if state.characters:
            character = state.characters[0]
            traits = "_".join(character.visual_traits[:2])
            return f"{character.character_id}:{character.name}:{traits}".lower()
        return "primary_subject"


class VLMFrameObserver:
    observer_id = "vlm_frame_observer"

    def __init__(
        self,
        describe_frame: Callable[[Path, dict[str, Any]], FrameObservation | dict[str, Any]],
        *,
        provider_id: str = "custom_vlm",
    ) -> None:
        self.describe_frame = describe_frame
        self.provider_id = provider_id
        self.observer_id = provider_id

    def observe(
        self,
        *,
        state: ProjectState,
        generated_shot: GeneratedShotResult,
        frame_paths: list[Path],
    ) -> list[FrameObservation]:
        observations: list[FrameObservation] = []
        targets = state.metadata.get("physical_targets", {})
        effect_targets = state.metadata.get("effect_demo_targets", {})
        context = {
            "project_id": state.project_id,
            "run_id": state.run_id,
            "shot_id": generated_shot.shot_id,
            "provider_id": self.provider_id,
            "physical_targets": targets,
            "required_elements": targets.get("required_elements")
            or effect_targets.get("required_elements")
            or [],
            "success_criteria": effect_targets.get("success_criteria", []),
        }
        for index, frame_path in enumerate(frame_paths):
            raw = self.describe_frame(frame_path, context)
            if isinstance(raw, FrameObservation):
                observation = raw
            else:
                observation = FrameObservation.model_validate(
                    {
                        "frame_index": index,
                        "frame_path": str(frame_path),
                        "source": self.provider_id,
                        **raw,
                    }
                )
            observations.append(observation)
        return observations
