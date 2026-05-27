from pathlib import Path

from shotforge.core.project_state import ProjectState, ShotSpec
from shotforge.exporters.mp4_exporter import MP4Exporter


def test_mp4_exporter_builds_ffmpeg_command(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = ProjectState(user_idea="test")
    state.shots = []
    artifact_dir = get_settings().runs_dir / state.run_id / "artifacts"
    artifact_dir.mkdir(parents=True)
    frame = artifact_dir / "shot_01.png"
    frame.write_bytes(b"png")
    state.shots.append(
        ShotSpec(
            shot_id="shot_01",
            scene_id="scene_01",
            index=1,
            title="Test",
            duration_seconds=4,
            description="Test shot",
            shot_type="wide",
        )
    )

    commands = []
    monkeypatch.setattr("shutil.which", lambda name: "ffmpeg" if name == "ffmpeg" else None)

    def fake_run(command, check, capture_output):
        commands.append(command)
        Path(command[-1]).write_bytes(b"mp4")

    monkeypatch.setattr("subprocess.run", fake_run)

    output = MP4Exporter().export(state)

    assert output.exists()
    assert commands
    assert "ffmpeg" in commands[0][0]
