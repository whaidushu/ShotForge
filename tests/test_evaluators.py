from shotforge.evaluators import (
    EvaluatorContext,
    FrameConsistencyEvaluator,
    PhysicalEffectEvaluator,
    PromptStaticEvaluator,
)
from shotforge.core.project_state import GeneratedResult, GeneratedShotResult
from shotforge.core.physical_targets import extract_physical_targets
from shotforge.core.rubrics import RubricRegistry
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.evaluation_workflow import run_evaluation, run_mock_generation


def test_prompt_static_evaluator_emits_prompt_signal(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A quiet revenge reveal in a luxury elevator",
        duration_seconds=24,
        language="en",
    )
    generated_result = run_mock_generation(state)
    rubric = RubricRegistry().load("baseline_v1")
    signals = PromptStaticEvaluator().evaluate(
        EvaluatorContext(state=state, generated_result=generated_result, rubric=rubric)
    )

    assert signals
    assert {signal.dimension_id for signal in signals} == {"prompt_executability"}
    assert all(signal.source == "prompt_static" for signal in signals)


def test_physical_effect_evaluator_emits_hard_fact_signals(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "Exactly two red robots inspect one blue cube in a clean studio",
        duration_seconds=24,
        language="en",
    )
    generated_result = run_mock_generation(state)
    generated_result.shots[0].mock_video_uri = "file://observed.mp4"
    generated_result.shots[0].metadata["generator_mode"] = "visual_observer"
    generated_result.shots[0].detected_elements = ["one red robot", "blue cube", "studio"]
    generated_result.shots[0].observed_summary = "The frame shows one red robot near a blue cube."
    rubric = RubricRegistry().load("baseline_v1")
    signals = PhysicalEffectEvaluator().evaluate(
        EvaluatorContext(state=state, generated_result=generated_result, rubric=rubric)
    )

    dimension_ids = {signal.dimension_id for signal in signals}
    assert {
        "subject_count",
        "color_alignment",
        "element_presence",
        "element_description",
    }.issubset(dimension_ids)
    count_signal = next(signal for signal in signals if signal.dimension_id == "subject_count")
    assert count_signal.score < 0.9
    assert count_signal.metadata["expected_subject_count"] == 2
    assert count_signal.metadata["observation_mode"] == "visual_observation"


def test_physical_target_extraction_for_cyber_cat_demo():
    targets = extract_physical_targets("一只赛博猫在雨夜上海屋顶追逐发光无人机", "zh")

    assert targets["required_elements"] == [
        "cyber cat",
        "glowing drone",
        "Shanghai",
        "rooftop",
        "rainy night",
    ]
    assert any(target["type"] == "action" and target["label"] == "chasing" for target in targets["targets"])
    assert targets["targets"][0]["count"] == 1


def test_design_prompt_injects_physical_targets_for_generation(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("一只赛博猫在雨夜上海屋顶追逐发光无人机", duration_seconds=8, language="zh")
    prompt = state.prompt_package.prompts[0]

    assert state.metadata["physical_targets"]["required_elements"] == [
        "cyber cat",
        "glowing drone",
        "Shanghai",
        "rooftop",
        "rainy night",
    ]
    assert state.metadata["effect_contract"]["targets"]
    assert state.metadata["effect_contract_stage"] == "intent_contract_extraction"
    assert state.prompt_package.metadata["effect_contract_id"] == state.metadata["effect_contract"]["contract_id"]
    assert "EFFECT CONTRACT" in prompt.prompt
    assert "MANDATORY VISIBLE ELEMENTS: cyber cat, glowing drone, Shanghai, rooftop, rainy night." in prompt.prompt
    assert prompt.structured_template is not None
    assert any("EFFECT CONTRACT" in item for item in prompt.structured_template.physical_constraints)
    assert any("glowing drone" in item for item in prompt.structured_template.physical_constraints)
    assert "missing cyber cat" in prompt.negative_prompt
    get_settings.cache_clear()


def test_physical_evaluator_flags_real_video_without_required_elements(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("一只赛博猫在雨夜上海屋顶追逐发光无人机", duration_seconds=8, language="zh")
    generated = GeneratedResult(
        project_id=state.project_id,
        run_id=state.run_id,
        version=state.version,
        provider="comfyui",
        status="completed",
        shots=[
            GeneratedShotResult(
                shot_id=state.shots[0].shot_id,
                prompt_id="prompt_1",
                mock_video_uri=str(tmp_path / "demo.mp4"),
                duration_seconds=8,
                observed_summary="ComfyUI generated a video but no visual detector confirmed the requested elements.",
                detected_elements=[],
            )
        ],
    )
    rubric = RubricRegistry().load("baseline_v1")
    signals = PhysicalEffectEvaluator().evaluate(
        EvaluatorContext(state=state, generated_result=generated, rubric=rubric)
    )
    element_signal = next(signal for signal in signals if signal.dimension_id == "element_presence")

    assert element_signal.score < 0.82
    assert element_signal.metadata["observation_mode"] == "real_video_unobserved"
    assert "cyber cat" in element_signal.metadata["missing_elements"]
    assert "glowing drone" in element_signal.metadata["missing_elements"]
    get_settings.cache_clear()


def test_frame_consistency_evaluator_detects_single_shot_drift(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A woman keeps the same face while lifting a red umbrella",
        duration_seconds=8,
        language="en",
    )
    generated_result = run_mock_generation(state)
    generated_result.shots[0].metadata["frame_observations"] = [
        {
            "frame_index": 0,
            "detected_elements": ["woman", "red umbrella"],
            "face_identity": "woman_a",
            "action_summary": "woman lifting umbrella",
        },
        {
            "frame_index": 8,
            "detected_elements": ["man", "blue backpack"],
            "face_identity": "man_b",
            "action_summary": "man walking away",
        },
    ]
    rubric = RubricRegistry().load("baseline_v1")
    signals = FrameConsistencyEvaluator().evaluate(
        EvaluatorContext(state=state, generated_result=generated_result, rubric=rubric)
    )

    by_dimension = {
        signal.dimension_id: signal
        for signal in signals
        if signal.shot_id == generated_result.shots[0].shot_id
    }
    assert by_dimension["frame_element_consistency"].score < 0.84
    assert by_dimension["frame_action_consistency"].score < 0.82
    assert by_dimension["face_identity_consistency"].score < 0.84
    assert by_dimension["face_identity_consistency"].metadata["single_shot_mode"] is False


def test_design_pipeline_builds_structured_prompt_template(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A quiet revenge reveal in a luxury elevator",
        duration_seconds=24,
        language="en",
    )
    template = state.prompt_package.prompts[0].structured_template

    assert template is not None
    assert template.character_identity
    assert template.scene_constraints
    assert template.physical_constraints
    assert template.action_sequence
    assert template.motion_direction
    assert template.success_criteria


def test_evaluation_report_exposes_layer_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A quiet revenge reveal in a luxury elevator",
        duration_seconds=24,
        language="en",
    )
    generated_result = run_mock_generation(state)
    report = run_evaluation(state, generated_result=generated_result)
    layers = report.score_card.metadata["layers"]

    assert layers
    assert [layer["layer_index"] for layer in layers] == sorted(
        layer["layer_index"] for layer in layers
    )
    assert any(layer["layer_id"] == "physical_effect" for layer in layers)
    assert any(layer["layer_id"] == "frame_consistency" for layer in layers)
    assert any(layer["layer_id"] == "style_color" for layer in layers)
    assert any(layer["layer_id"] == "emotion_atmosphere" for layer in layers)
    assert all("layer_id" in issue.metadata for issue in report.issues)
    assert all("prompt_fields" in issue.metadata for issue in report.issues)
    target_summary = report.metadata["physical_target_summary"]
    assert target_summary["generated_result_id"] == generated_result.generated_result_id
    assert "observer_ids" in target_summary
    assert "required_elements" in target_summary
    assert "hard_issue_count" in target_summary
    assert target_summary["observation_confidence_note"].startswith("Use a VLM observer")
