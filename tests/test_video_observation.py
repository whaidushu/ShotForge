from pathlib import Path

from shotforge.observation import VLMFrameObserver, VideoFrameExtractor, VideoObservationService
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.evaluation_workflow import run_generation, run_evaluation_pipeline


def test_video_observation_backfills_prompt_proxy_frames(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setattr("shutil.which", lambda name: None)

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A woman keeps the same face while lifting a red umbrella",
        duration_seconds=8,
        language="en",
    )
    generated = run_generation(state, provider_id="mock")

    VideoObservationService().observe_result(state, generated)

    observations = generated.shots[0].metadata["frame_observations"]
    assert len(observations) == 3
    assert len(generated.shots[0].frame_observations) == 3
    assert state.observation_reports
    assert generated.observation_report_id == state.observation_reports[-1].report_id
    assert state.observation_reports[-1].sequence_observations
    assert observations[0]["source"] == "heuristic_frame_observer"
    assert observations[0]["metadata"]["observation_mode"] == "prompt_proxy"
    assert generated.metadata["frame_observation_count"] >= 3


def test_video_frame_extractor_uses_ffmpeg_when_available(tmp_path, monkeypatch):
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"mp4")
    output_dir = tmp_path / "frames"
    commands = []
    monkeypatch.setattr("shutil.which", lambda name: "ffmpeg" if name == "ffmpeg" else None)

    def fake_run(command, check, capture_output):
        commands.append(command)
        output_dir.mkdir(parents=True, exist_ok=True)
        for index in range(1, 3):
            (output_dir / f"frame_{index:03d}.jpg").write_bytes(b"jpg")

    monkeypatch.setattr("subprocess.run", fake_run)

    frames = VideoFrameExtractor(sample_count=2).extract(video_path, output_dir)

    assert len(frames) == 2
    assert all(isinstance(frame, Path) for frame in frames)
    assert commands
    assert commands[0][0] == "ffmpeg"


def test_evaluation_pipeline_observes_generated_result(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setattr("shutil.which", lambda name: None)

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A woman keeps the same face while lifting a red umbrella",
        duration_seconds=8,
        language="en",
    )
    run_evaluation_pipeline(state, generator_provider_id="mock", export=False)

    generated = state.generation_results[-1]
    assert generated.metadata["frame_observation_provider"] == "heuristic_frame_observer"
    assert generated.observation_report_id
    assert state.observation_reports[-1].shot_observations[0].frame_observations
    assert generated.shots[0].metadata["frame_observations"]
    assert "frame_consistency_static" in state.evaluation_reports[-1].metadata["evaluator_sources"]


def test_vlm_observer_adapts_frame_descriptions(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setattr("shutil.which", lambda name: None)

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A red umbrella opens beside a woman", duration_seconds=8, language="en")
    generated = run_generation(state, provider_id="mock")
    frame = tmp_path / "frame.jpg"
    frame.write_bytes(b"jpg")

    observer = VLMFrameObserver(
        lambda frame_path, context: {
            "detected_elements": ["woman", "red umbrella"],
            "face_identity": "woman_a",
            "action_summary": "opens umbrella",
            "confidence": 0.91,
            "metadata": {"context_shot": context["shot_id"]},
        },
        provider_id="test_vlm",
    )
    observations = observer.observe(
        state=state,
        generated_shot=generated.shots[0],
        frame_paths=[frame],
    )

    assert observations[0].source == "test_vlm"
    assert observations[0].detected_elements == ["woman", "red umbrella"]
    assert observations[0].metadata["context_shot"] == generated.shots[0].shot_id
