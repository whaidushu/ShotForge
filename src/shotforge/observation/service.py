from __future__ import annotations

from pathlib import Path
from statistics import mean

from shotforge.config import get_settings
from shotforge.core.project_state import (
    FrameObservation,
    GeneratedResult,
    GeneratedShotResult,
    ObservationReport,
    ProjectState,
    ShotObservation,
)
from shotforge.observation.extractors import VideoFrameExtractor
from shotforge.observation.observers import FrameObserver
from shotforge.observation.providers import build_configured_frame_observer
from shotforge.observation.sequence import SequenceObservationBuilder


class VideoObservationService:
    def __init__(
        self,
        *,
        extractor: VideoFrameExtractor | None = None,
        observer: FrameObserver | None = None,
        sequence_builder: SequenceObservationBuilder | None = None,
    ) -> None:
        self.extractor = extractor or VideoFrameExtractor(
            sample_count=get_settings().vlm_frame_sample_count
        )
        self.observer = observer or build_configured_frame_observer()
        self.sequence_builder = sequence_builder or SequenceObservationBuilder()

    def observe_result(self, state: ProjectState, generated_result: GeneratedResult) -> GeneratedResult:
        shot_observations = []
        for generated_shot in generated_result.shots:
            self.observe_shot(state, generated_shot)
            shot_observations.append(self._shot_observation(state, generated_result, generated_shot))
        sequence_observations = self.sequence_builder.build(generated_result)
        report = ObservationReport(
            project_id=state.project_id,
            run_id=state.run_id,
            version=state.version,
            generated_result_id=generated_result.generated_result_id,
            observer_id=self.observer.observer_id,
            shot_observations=shot_observations,
            sequence_observations=sequence_observations,
            metadata={
                "shot_count": len(shot_observations),
                "frame_observation_count": sum(
                    len(shot.frame_observations) for shot in generated_result.shots
                ),
            },
        )
        state.observation_reports.append(report)
        generated_result.observation_report_id = report.report_id
        generated_result.metadata["frame_observation_provider"] = self.observer.observer_id
        generated_result.metadata["frame_observation_count"] = sum(
            len(shot.frame_observations)
            for shot in generated_result.shots
        )
        generated_result.metadata["observation_report_id"] = report.report_id
        state.touch()
        return generated_result

    def observe_shot(
        self,
        state: ProjectState,
        generated_shot: GeneratedShotResult,
    ) -> list[FrameObservation]:
        video_path = self._video_path(generated_shot)
        frame_dir = self._frame_dir(state, generated_shot)
        frame_paths = self.extractor.extract(video_path, frame_dir) if video_path else []
        observations = self.observer.observe(
            state=state,
            generated_shot=generated_shot,
            frame_paths=frame_paths,
        )
        generated_shot.frame_observations = observations
        generated_shot.metadata["frame_observations"] = [
            observation.model_dump(mode="json")
            for observation in observations
        ]
        generated_shot.metadata["frame_observation_provider"] = self.observer.observer_id
        generated_shot.metadata["frame_observation_count"] = len(observations)
        generated_shot.metadata["frame_observation_dir"] = str(frame_dir) if frame_paths else ""
        return observations

    def _shot_observation(
        self,
        state: ProjectState,
        generated_result: GeneratedResult,
        generated_shot: GeneratedShotResult,
    ) -> ShotObservation:
        elements = sorted(
            {
                element
                for observation in generated_shot.frame_observations
                for element in observation.detected_elements
            }
        )
        confidence_values = [item.confidence for item in generated_shot.frame_observations]
        return ShotObservation(
            shot_id=generated_shot.shot_id,
            generated_result_id=generated_result.generated_result_id,
            version=state.version,
            observer_id=self.observer.observer_id,
            summary=generated_shot.observed_summary,
            frame_observations=generated_shot.frame_observations,
            detected_elements=elements or generated_shot.detected_elements,
            action_summary=generated_shot.motion_summary,
            confidence=round(mean(confidence_values), 3) if confidence_values else 0.0,
            metadata={
                "prompt_id": generated_shot.prompt_id,
                "frame_count": len(generated_shot.frame_observations),
            },
        )

    def _video_path(self, generated_shot: GeneratedShotResult) -> Path | None:
        candidates = [
            str(generated_shot.metadata.get("artifact_path", "")),
            str(generated_shot.metadata.get("artifact_uri", "")),
            generated_shot.mock_video_uri,
        ]
        for candidate in candidates:
            if not candidate or "://" in candidate:
                continue
            path = Path(candidate)
            if path.exists():
                return path
        return None

    def _frame_dir(self, state: ProjectState, generated_shot: GeneratedShotResult) -> Path:
        iteration = str(generated_shot.metadata.get("iteration") or f"v{generated_shot.prompt_id}")
        return (
            get_settings().runs_dir
            / state.run_id
            / "iterations"
            / iteration
            / "frames"
            / generated_shot.shot_id
        )
