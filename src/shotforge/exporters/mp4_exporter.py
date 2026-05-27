from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from shotforge.config import get_settings
from shotforge.core.project_state import ProjectState


class MP4Exporter:
    def export(
        self,
        state: ProjectState,
        *,
        aspect_ratio: str = "16:9",
        fps: int = 24,
        crf: int = 23,
    ) -> Path:
        self._ensure_ffmpeg()
        run_dir = get_settings().runs_dir / state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        output_path = run_dir / f"{state.run_id}_{aspect_ratio.replace(':', 'x')}.mp4"
        frames = self._collect_artifacts(state, run_dir / "artifacts")
        if not frames:
            raise FileNotFoundError(
                f"No local generated artifacts found for run {state.run_id}. "
                "Run a real or local generator before MP4 export."
            )
        self._stitch(frames, output_path, fps=fps, crf=crf, aspect_ratio=aspect_ratio)
        return output_path

    def _collect_artifacts(self, state: ProjectState, artifacts_dir: Path) -> list[Path]:
        paths_by_shot = self._paths_from_generation_results(state)
        frames: list[Path] = []
        for shot in state.shots:
            if shot.shot_id in paths_by_shot:
                frames.append(paths_by_shot[shot.shot_id])
                continue
            if artifacts_dir.exists():
                candidates = sorted(artifacts_dir.glob(f"{shot.shot_id}.*"))
                if candidates:
                    frames.append(candidates[0])
        return frames

    def _paths_from_generation_results(self, state: ProjectState) -> dict[str, Path]:
        if not state.generation_results:
            return {}
        paths: dict[str, Path] = {}
        for shot in state.generation_results[-1].shots:
            candidates = [
                str(shot.metadata.get("artifact_path", "")),
                str(shot.metadata.get("artifact_uri", "")),
                shot.mock_video_uri,
            ]
            for candidate in candidates:
                path = Path(candidate)
                if path.exists():
                    paths[shot.shot_id] = path
                    break
        return paths

    def _stitch(
        self,
        frames: list[Path],
        output_path: Path,
        *,
        fps: int,
        crf: int,
        aspect_ratio: str,
    ) -> None:
        concat_list = output_path.with_suffix(".concat.txt")
        lines = []
        for frame in frames:
            lines.append(f"file '{frame.as_posix()}'")
            lines.append("duration 4")
        lines.append(f"file '{frames[-1].as_posix()}'")
        concat_list.write_text("\n".join(lines), encoding="utf-8")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_list),
                    "-vf",
                    f"{self._scale_filter(aspect_ratio)},fps={fps}",
                    "-c:v",
                    "libx264",
                    "-crf",
                    str(crf),
                    "-pix_fmt",
                    "yuv420p",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
        finally:
            concat_list.unlink(missing_ok=True)

    def _scale_filter(self, aspect_ratio: str) -> str:
        targets = {
            "16:9": "1280:720",
            "9:16": "720:1280",
            "1:1": "720:720",
        }
        target = targets.get(aspect_ratio)
        if target is None:
            raise ValueError("aspect_ratio must be one of: 16:9, 9:16, 1:1")
        return f"scale={target}:force_original_aspect_ratio=decrease,pad={target}:(ow-iw)/2:(oh-ih)/2"

    def _ensure_ffmpeg(self) -> None:
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg is required for MP4 export but was not found on PATH.")
