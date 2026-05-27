from __future__ import annotations

import csv
from pathlib import Path

from shotforge.core.project_state import ExportArtifact, ProjectState
from shotforge.l10n import t


def export_csv(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "package.csv"
    fieldnames = [
        "shot_id",
        "scene_id",
        "title",
        "duration_seconds",
        "description",
        "shot_type",
        "camera",
        "subject_motion",
        "music",
        "prompt",
    ]
    headers = {
        "shot_id": "shot_id" if state.language == "en" else "镜头ID",
        "scene_id": "scene_id" if state.language == "en" else "场景ID",
        **t(state.language, "csv_headers"),
    }
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writerow(headers)
        for shot in state.shots:
            audio = next((item for item in state.audio_cues if item.shot_id == shot.shot_id), None)
            prompt = next(
                (item for item in state.prompt_package.prompts if item.shot_id == shot.shot_id),
                None,
            )
            writer.writerow(
                {
                    "shot_id": shot.shot_id,
                    "scene_id": shot.scene_id,
                    "title": shot.title,
                    "duration_seconds": shot.duration_seconds,
                    "description": shot.description,
                    "shot_type": shot.shot_type,
                    "camera": shot.motion.camera if shot.motion else "",
                    "subject_motion": shot.motion.subject_motion if shot.motion else "",
                    "music": audio.music if audio else "",
                    "prompt": prompt.prompt if prompt else "",
                }
            )
    _record(state, "csv", path)
    return path


def _record(state: ProjectState, export_format: str, path: Path) -> None:
    state.exports = [item for item in state.exports if item.format != export_format]
    state.exports.append(ExportArtifact(format=export_format, path=str(path)))
    state.touch()
