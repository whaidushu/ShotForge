from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline
from shotforge.workflows.redesign_workflow import run_redesign
from shotforge.core.packages import ProjectPackageView
from shotforge.core.project_state import ProjectState
from shotforge.core.solution_playbook import SolutionPlaybookStore


def test_solution_playbooks_load_from_package():
    playbooks = SolutionPlaybookStore().load()

    assert {item.playbook_id for item in playbooks} >= {
        "media_advertising_video_ops",
        "gaming_character_content",
        "ecommerce_product_video",
    }
    assert SolutionPlaybookStore().find_for_industry("Gaming").playbook_id == "gaming_character_content"


def test_pipeline_exports_all_formats(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A robot chef films a moonlit dessert commercial", duration_seconds=24)

    assert "language" not in state.model_dump(mode="json")
    assert state.creative_intent is not None
    assert len(state.scenes) == 4
    assert len(state.shots) == 4
    assert len(state.motion_plan) == 4
    assert len(state.audio_cues) == 4
    assert len(state.prompt_package.prompts) == 4
    assert state.solution_architecture is not None
    assert state.solution_architecture.components
    assert state.solution_architecture.poc_success_criteria
    assert "media_advertising_video_ops" in state.solution_architecture.knowledge_assets
    assert state.solution_architecture.scenario_patterns
    assert state.solution_architecture.evaluation_metrics
    assert state.delivery_readiness is not None
    assert state.delivery_readiness.overall_status == "warning"
    assert {check.check_id for check in state.delivery_readiness.checks} >= {
        "state_schema",
        "state_transition_audit",
        "context_safety",
        "mcp_capability",
        "memory_strategy",
        "solution_architecture",
        "provider_strategy",
        "evaluation_loop",
    }
    assert {item.format for item in state.exports} == {
        "json",
        "csv",
        "markdown",
        "manifest",
        "package_view",
        "trace",
        "run_summary",
    }
    for artifact in state.exports:
        assert artifact.path


def test_csv_export_is_excel_friendly_for_chinese(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("一只赛博猫在雨夜上海屋顶追逐发光无人机", duration_seconds=24)
    csv_path = next(item.path for item in state.exports if item.format == "csv")
    raw = open(csv_path, "rb").read()

    assert raw.startswith(b"\xef\xbb\xbf")
    assert "一只赛博猫" in raw.decode("utf-8-sig")
    assert "镜头ID" in raw.decode("utf-8-sig")


def test_pipeline_supports_english_output(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A neon train crossing a desert at sunrise",
        duration_seconds=24,
        language="en",
    )
    csv_path = next(item.path for item in state.exports if item.format == "csv")
    markdown_path = next(item.path for item in state.exports if item.format == "markdown")
    manifest_path = next(item.path for item in state.exports if item.format == "manifest")
    trace_path = next(item.path for item in state.exports if item.format == "trace")
    summary_path = next(item.path for item in state.exports if item.format == "run_summary")

    assert "language" not in state.model_dump(mode="json")
    assert state.solution_architecture is not None
    assert state.solution_architecture.industry == "Media and Entertainment"
    assert state.delivery_readiness is not None
    assert any(
        item.criterion_id == "poc_observability"
        for item in state.solution_architecture.poc_success_criteria
    )
    assert state.shots[0].title == "Hook"
    assert "Visual style" in state.prompt_package.prompts[0].prompt
    assert "shot_id" in open(csv_path, encoding="utf-8-sig").read()
    assert "ShotForge Production Package" in open(markdown_path, encoding="utf-8").read()
    assert "Solution Architecture" in open(markdown_path, encoding="utf-8").read()
    assert "Delivery Readiness" in open(markdown_path, encoding="utf-8").read()
    assert "audit_api" in open(manifest_path, encoding="utf-8").read()
    assert '"language"' not in open(manifest_path, encoding="utf-8").read()
    assert "harness_audit" in open(trace_path, encoding="utf-8").read()
    summary = open(summary_path, encoding="utf-8").read()
    assert "ShotForge Run Summary" in summary
    assert "Harness Evidence" in summary
    assert "State transitions" in summary


def test_chinese_idea_is_preserved_in_storyboard_text(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    idea = "\u4e00\u4e2a\u5973\u4e3b\u5728\u96e8\u591c\u5929\u53f0\u64ad\u653e\u5f55\u97f3\u5b8c\u6210\u53cd\u8f6c"
    state = run_design_pipeline(idea, duration_seconds=24, language="zh")

    assert state.user_idea == idea
    assert idea in state.shots[1].description
    assert "????" not in state.shots[1].description
    assert "\\u" not in state.shots[1].description


def test_elevator_revenge_storyboard_uses_concrete_beats(tmp_path, monkeypatch):
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

    descriptions = " ".join(shot.description for shot in state.shots)
    assert "Hook beat for" not in descriptions
    assert "black access card" in descriptions
    assert "hidden scanner" in descriptions
    assert "security footage" in descriptions
    assert "empty boardroom on floor 88" in descriptions
    assert state.shots[1].metadata["story_beat"]["action_upgrade"].startswith("Make the card tap")
    assert state.shots[1].motion is not None
    assert "floor number jump" in state.shots[1].motion.subject_motion
    assert "scanner beep" in state.audio_cues[1].sound_design


def test_full_loop_generates_mock_evaluation(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline(
        "一只赛博猫在雨夜上海屋顶追逐发光无人机",
        duration_seconds=24,
        language="zh",
        generator_provider_id="mock",
    )
    report = state.evaluation_reports[-1]
    evaluation_csv_path = next(item.path for item in state.exports if item.format == "evaluation_csv")
    markdown_path = next(item.path for item in state.exports if item.format == "markdown")

    assert len(state.generation_results) == 1
    assert state.metadata["generator_provider_id"] == "mock"
    assert state.generation_results[-1].metadata["provider_id"] == "mock"
    assert len(report.score_card.dimension_scores) >= 9
    assert "physical_effect_static" in report.metadata["evaluator_sources"]
    assert "frame_consistency_static" in report.metadata["evaluator_sources"]
    assert "mock_visual" in report.metadata["evaluator_sources"]
    assert "prompt_static" in report.metadata["evaluator_sources"]
    assert report.metadata["signal_count"] >= len(report.score_card.dimension_scores)
    assert report.issues
    assert all(issue.correction_type for issue in report.issues)
    assert all(issue.metadata.get("signal_source") for issue in report.issues)
    assert "action_clarity" in {score.dimension_id for score in report.score_card.dimension_scores}
    assert "evaluation_id" in open(evaluation_csv_path, encoding="utf-8-sig").read()
    assert "Evaluation Report" in open(markdown_path, encoding="utf-8").read()


def test_redesign_uses_story_beat_specific_revision_notes(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline(
        "A quiet revenge reveal in a luxury elevator",
        duration_seconds=24,
        language="en",
        generator_provider_id="mock",
    )
    next_state = run_redesign(state, report=state.evaluation_reports[-1], generator_provider_id="mock")
    patch_values = [
        str(operation.value)
        for patch in next_state.correction_patches
        for operation in patch.operations
    ]

    assert any("Revision target for shot_02" in value for value in patch_values)
    assert any("card tap, floor jump, and briefcase reveal" in value for value in patch_values)
    assert any("Keep these visible anchors measurable" in value for value in patch_values)


def test_project_package_view_keeps_state_as_aggregate(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline(
        "A red umbrella opens in a rainy street",
        duration_seconds=8,
        language="en",
        generator_provider_id="mock",
    )
    view = ProjectPackageView.from_state(state)

    assert view.project_id == state.project_id
    assert view.design.prompt_package == state.prompt_package
    assert view.generation.generation_results == state.generation_results
    assert view.observation.observation_reports == state.observation_reports
    assert view.evaluation.evaluation_reports == state.evaluation_reports
    assert view.runtime.exports == state.exports


def test_template_package_metadata_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings
    from shotforge.exporters import ExportManager

    get_settings.cache_clear()
    state = run_design_pipeline("A quiet revenge reveal in a luxury elevator", language="en")
    state.shots[0].metadata["visual_anchor"] = "phone recording close-up"
    state.audio_cues[0].metadata["audio_anchor"] = "music drops to silence"
    state.prompt_package.metadata["template_experiment"] = "anchor_fields_v0"
    json_path = ExportManager().export_json(state)

    loaded = ProjectState.model_validate_json(json_path.read_text(encoding="utf-8"))

    assert loaded.shots[0].metadata["visual_anchor"] == "phone recording close-up"
    assert loaded.audio_cues[0].metadata["audio_anchor"] == "music drops to silence"
    assert loaded.prompt_package.metadata["template_experiment"] == "anchor_fields_v0"


def test_redesign_injects_effect_contracts_into_executable_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline(
        "A cyber cat chases a glowing neon drone on a rainy Shanghai rooftop",
        duration_seconds=8,
        language="en",
        generator_provider_id="mock",
    )
    before_report = state.evaluation_reports[-1]

    next_state = run_redesign(state, report=before_report, generator_provider_id="mock")

    changed_prompts = [
        prompt
        for prompt in next_state.prompt_package.prompts
        if "EFFECT CONTRACT" in prompt.prompt
    ]
    assert changed_prompts
    prompt = changed_prompts[0]
    assert "ACTION" in prompt.prompt or "COLOR LOCK" in prompt.prompt
    assert prompt.structured_template is not None
    assert any("frame" in item.lower() for item in prompt.structured_template.success_criteria)
    assert any(
        term in prompt.negative_prompt
        for term in ["action morphing", "missing glow", "object morphing"]
    )
    assert next_state.score_deltas[-1].overall_delta >= 0
    get_settings.cache_clear()


def test_gold_sample_package_is_public_and_loadable():
    samples = [
        ("shotforge_gold_sample", "hidden scanner"),
        ("shotforge_gold_sample_zh", "隐藏扫描器"),
    ]
    for run_id, expected_text in samples:
        package_path = f"examples/demo_runs/{run_id}/package.json"
        raw = open(package_path, encoding="utf-8").read()

        assert "D:\\\\" not in raw
        assert "_private" not in raw

        state = ProjectState.model_validate_json(raw)
        assert "language" not in state.model_dump(mode="json")
        assert state.run_id == run_id
        assert state.version >= 3
        assert state.metadata["demo_sample"] is True
        assert state.evaluation_reports[-1].score_card.overall_score >= 0.8
        assert expected_text in state.shots[1].description
        assert len(state.version_diffs) >= 2
