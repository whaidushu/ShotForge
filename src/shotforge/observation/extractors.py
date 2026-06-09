from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class VideoFrameExtractor:
    def __init__(self, *, sample_count: int = 4, scale_width: int = 320) -> None:
        self.sample_count = sample_count
        self.scale_width = scale_width

    def extract(self, video_path: Path, output_dir: Path) -> list[Path]:
        ffmpeg = self._ffmpeg_path()
        if not video_path.exists() or ffmpeg is None:
            return []
        output_dir.mkdir(parents=True, exist_ok=True)
        pattern = output_dir / "frame_%03d.jpg"
        try:
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(video_path),
                    "-vf",
                    f"fps=1,scale={self.scale_width}:-1",
                    "-frames:v",
                    str(self.sample_count),
                    str(pattern),
                ],
                check=True,
                capture_output=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return []
        return sorted(output_dir.glob("frame_*.jpg"))[: self.sample_count]

    def _ffmpeg_path(self) -> str | None:
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg
        try:
            import imageio_ffmpeg
        except ImportError:
            return None
        return imageio_ffmpeg.get_ffmpeg_exe()
