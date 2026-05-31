from shotforge.core.convergence_engine import ConvergenceEngine
from shotforge.core.project_state import FieldChange, ProjectState, RegressionCheck, ScoreDelta, VersionDiff
from shotforge.core.version_diff import VersionDiffBuilder
from shotforge.core.version_manager import VersionManager
from shotforge.agents.correction import build_default_correction_registry
from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline
from shotforge.workflows.iterative_redesign_workflow import run_iterative_redesign
from shotforge.workflows.redesign_planning_workflow import run_redesign_planning
from shotforge.workflows.redesign_workflow import run_redesign


def test_redesign_planning_creates_correction_plans(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline("A neon train crossing a desert at sunrise", language="en")
    plans = run_redesign_planning(state)

    assert plans
    assert state.redesign_plans
    target_layer = state.redesign_plans[-1].target_layer_index
    assert state.correction_plans
    assert all(plan.selected_agent.endswith("_correction_agent") for plan in plans)
    assert all(plan.target_issue_ids for plan in plans)
    assert all(plan.metadata["layer_index"] == target_layer for plan in plans)
    assert any("prompt_package.prompts" in field for plan in plans for field in plan.affected_fields)


def test_redesign_planning_localizes_chinese_plan_text(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline("一只赛博猫在雨夜上海屋顶追逐发光无人机", language="zh")
    plans = run_redesign_planning(state)

    assert plans
    assert any("修正" in plan.correction_strategy for plan in plans)
    assert any("可能" in plan.risk for plan in plans)


def test_fork_next_version_preserves_history_and_clears_run_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline("A neon train crossing a desert at sunrise", language="en")
    next_state = VersionManager().fork_next_version(state, reason="test_redesign")

    assert next_state.version == state.version + 1
    assert next_state.exports == []
    assert next_state.trace_logs == []
    assert next_state.issue_history == state.issue_history
    assert next_state.evaluation_reports == state.evaluation_reports
    assert next_state.metadata["parent_version"] == state.version
    assert next_state.metadata["fork_reason"] == "test_redesign"


def test_version_diff_builder_tracks_changed_prompt_and_issues(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline("A neon train crossing a desert at sunrise", language="en")
    next_state = VersionManager().fork_next_version(state)
    next_state.prompt_package.prompts[0].prompt += " Add a stronger visual anchor."
    resolved_issue = next_state.issue_history.pop(0)

    diff = VersionDiffBuilder().build(
        state,
        next_state,
        explanation="Test targeted prompt update.",
    )

    assert diff.from_version == state.version
    assert diff.to_version == next_state.version
    assert "shot_01" in diff.changed_prompts
    assert resolved_issue.issue_id in diff.resolved_issues
    assert diff.field_changes


def test_redesign_workflow_applies_structured_patches(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline("A neon train crossing a desert at sunrise", language="en")
    next_state = run_redesign(state)

    assert next_state.version == 2
    assert next_state.metadata["redesign_result"]["patch_count"] > 0
    assert next_state.correction_patches
    assert next_state.version_diffs
    assert len(next_state.evaluation_reports) >= 2
    assert next_state.verification_reports
    assert next_state.score_deltas
    assert next_state.regression_checks
    assert next_state.score_deltas[-1].to_version == 2
    assert next_state.regression_checks[-1].to_version == 2
    assert any(plan.status == "applied" for plan in next_state.correction_plans)
    assert not next_state.metadata.get("skipped_correction_plan_ids")
    assert next_state.version_diffs[-1].changed_prompts


def test_redesign_prompt_patch_does_not_embed_issue_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline(
        "\u4e00\u4e2a\u5973\u4e3b\u5728\u96e8\u591c\u5929\u53f0\u64ad\u653e\u5f55\u97f3\u5b8c\u6210\u53cd\u8f6c",
        language="zh",
    )
    next_state = run_redesign(state)
    prompt_changes = [
        change
        for change in next_state.version_diffs[-1].field_changes
        if change.path.startswith("prompt_package.prompts")
    ]

    assert prompt_changes
    assert all("目标问题" not in str(change.after) for change in prompt_changes)
    assert all("prompt 可执行性不足" not in str(change.after) for change in prompt_changes)
    assert all("澄清可执行提示约束" not in str(change.after) for change in prompt_changes)
    assert any(
        "EFFECT CONTRACT" in str(change.after)
        or "PHYSICAL TARGETS" in str(change.after)
        or "MANDATORY VISIBLE ELEMENTS" in str(change.after)
        for change in prompt_changes
    )


def test_iterative_redesign_can_advance_beyond_v2(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline("A neon train crossing a desert at sunrise", language="en")
    final_state = run_iterative_redesign(
        state,
        max_iterations=2,
        min_delta=0.0,
        generator_provider_id="mock",
    )

    assert final_state.version == 3
    assert final_state.metadata["generator_provider_id"] == "mock"
    assert all(result.metadata["provider_id"] == "mock" for result in final_state.generation_results)
    assert len(final_state.convergence_steps) == 2
    assert [step.to_version for step in final_state.convergence_steps] == [2, 3]
    assert len(final_state.score_deltas) == 2
    assert len(final_state.regression_checks) == 2
    assert final_state.metadata["convergence_summary"]["latest_version"] == 3
    assert len(final_state.versions) >= 3


def test_iterative_redesign_uses_selected_iteration_count_as_upper_bound(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_full_loop_pipeline("A neon train crossing a desert at sunrise", language="en")
    final_state = run_iterative_redesign(
        state,
        max_iterations=4,
        min_delta=0.0,
        generator_provider_id="mock",
    )

    assert 2 <= final_state.version <= 5
    assert 1 <= len(final_state.convergence_steps) <= 4
    assert final_state.metadata["convergence_summary"]["latest_version"] == final_state.version
    assert final_state.convergence_steps[-1].stop_reason in {
        "design_package_unchanged",
        "selected_iterations_reached",
        "all_tracked_issues_resolved",
    }


def test_convergence_stops_when_design_package_is_unchanged():
    state = ProjectState(user_idea="No-op redesign")
    state.score_deltas.append(
        ScoreDelta(
            from_version=3,
            to_version=4,
            before_evaluation_id="eval_3",
            after_evaluation_id="eval_4",
            overall_before=0.7,
            overall_after=0.7,
            overall_delta=0.0,
        )
    )
    state.regression_checks.append(
        RegressionCheck(
            from_version=3,
            to_version=4,
            status="unchanged",
            summary="No evaluation movement.",
        )
    )
    state.version_diffs.append(
        VersionDiff(
            from_version=3,
            to_version=4,
            field_changes=[
                FieldChange(
                    path="metadata",
                    before={"iteration": 2},
                    after={"iteration": 3},
                    change_type="modified",
                )
            ],
        )
    )

    engine = ConvergenceEngine(max_iterations=10)
    stop_condition = engine.evaluate_stop_condition(state, iteration_index=3)
    step = engine.record_step(state, stop_condition)

    assert stop_condition.should_stop
    assert stop_condition.reason == "design_package_unchanged"
    assert step.stop_reason == "design_package_unchanged"
    assert step.metadata["meaningful_change_count"] == 0


def test_default_correction_registry_covers_baseline_types():
    registry = build_default_correction_registry()

    assert set(registry.list()) >= {
        "action",
        "audio",
        "camera",
        "character",
        "emotion",
        "prompt",
        "scene",
    }
