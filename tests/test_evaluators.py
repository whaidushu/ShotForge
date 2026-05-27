from shotforge.evaluators import EvaluatorContext, PromptStaticEvaluator
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
    assert any(layer["layer_id"] == "hard_targets" for layer in layers)
    assert all("layer_id" in issue.metadata for issue in report.issues)
    assert all("prompt_fields" in issue.metadata for issue in report.issues)
