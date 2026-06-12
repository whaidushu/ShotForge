from pathlib import Path

from shotforge.observation import VLMFrameObserver, VideoFrameExtractor, VideoObservationService
from shotforge.observation.providers.vlm import _observation_payload
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
    assert observations[0].target_checks == []
    assert observations[0].metadata["context_shot"] == generated.shots[0].shot_id


def test_vlm_observer_preserves_target_checks(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setattr("shutil.which", lambda name: None)

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A robot dog chases a glowing drone", duration_seconds=8, language="en")
    state.metadata["effect_contract"] = {
        "targets": [
            {
                "target_id": "object.glowing_drone",
                "label": "glowing drone",
                "target_type": "object",
            }
        ]
    }
    generated = run_generation(state, provider_id="mock")
    frame = tmp_path / "frame.jpg"
    frame.write_bytes(b"jpg")

    observer = VLMFrameObserver(
        lambda frame_path, context: {
            "detected_elements": [],
            "target_checks": [
                {
                    "target_id": "object.glowing_drone",
                    "label": "glowing drone",
                    "target_type": "object",
                    "visible": False,
                    "score": 0.2,
                    "evidence": "No drone is visible in the frame.",
                    "failure_reason": "model_ignored",
                    "suggested_repair": "separate the drone from background neon",
                    "confidence": 0.8,
                }
            ],
            "confidence": 0.8,
        },
        provider_id="test_vlm",
    )

    observations = observer.observe(
        state=state,
        generated_shot=generated.shots[0],
        frame_paths=[frame],
    )

    context_targets = state.metadata["effect_contract"]["targets"]
    assert context_targets
    assert context_targets[0]["target_id"] == "object.glowing_drone"
    assert observations[0].target_checks[0].target_id == "object.glowing_drone"
    assert observations[0].target_checks[0].failure_reason == "model_ignored"


def test_vlm_observation_payload_falls_back_from_thinking_text():
    content = """
    The frame shows a cat and rain on a wet rooftop.
    - cyber cat: not visible as a cybernetic subject.
    - glowing drone: visible ahead of the cat with cyan light.
    - rain: visible as streaks and puddle reflections.
    - Shanghai landmark skyline: missing, only a generic city skyline appears.
    """
    payload = _observation_payload(
        content,
        {
            "provider_id": "ollama-vision",
            "required_elements": [
                "cyber cat",
                "glowing drone",
                "rain",
                "Shanghai landmark skyline",
            ],
        },
    )

    assert payload["detected_elements"] == ["glowing drone", "rain"]
    assert payload["target_checks"]
    assert any(check["label"] == "glowing drone" and check["visible"] for check in payload["target_checks"])
    assert payload["face_identity"] == ""
    assert payload["confidence"] > 0
    assert "Shanghai landmark skyline" in payload["metadata"]["evidence"]


def test_vlm_observation_payload_accepts_explicit_target_checks():
    payload = _observation_payload(
        """
        {
          "detected_elements": [],
          "target_checks": [
            {
              "target_id": "setting.shanghai_rooftop",
              "label": "Shanghai rooftop",
              "target_type": "setting",
              "visible": false,
              "score": 0.18,
              "evidence": "A rooftop is present but no Shanghai landmark is visible.",
              "failure_reason": "prompt_weak",
              "suggested_repair": "add Oriental Pearl Tower and Lujiazui skyline",
              "confidence": 0.83
            }
          ],
          "confidence": 0.83,
          "evidence": "checked target contracts"
        }
        """,
        {"provider_id": "test-vlm", "required_elements": ["Shanghai rooftop"]},
    )

    check = payload["target_checks"][0]
    assert check["target_id"] == "setting.shanghai_rooftop"
    assert check["score"] == 0.18
    assert check["failure_reason"] == "prompt_weak"
