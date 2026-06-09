from shotforge.core.physical_convergence import (
    build_revision_plan_from_target_evaluation,
    candidate_gate,
    compare_report_target_evaluations,
)


def test_physical_candidate_gate_rejects_locked_regression():
    revision_plan = {
        "source_iteration": "v2",
        "target_iteration": "v3",
        "convergence_strategy": {"locked_targets": ["rain"]},
    }

    gate = candidate_gate(
        source_score=0.8,
        candidate_score=0.78,
        regressed_targets=["rain"],
        unresolved_targets=[],
        revision_plan=revision_plan,
    )

    assert gate["candidate_status"] == "rejected"
    assert gate["accepted_iteration"] == "v2"
    assert gate["rejected_iteration"] == "v3"
    assert gate["locked_regressions"] == ["rain"]


def test_physical_revision_plan_tracks_repairs_and_locks():
    evaluation = {
        "iteration": "v2",
        "target_scores": [
            {"target": "cyber cat", "score": 0.3, "frame_hits": [], "sampled_frame_count": 4},
            {"target": "rain", "score": 0.9, "frame_hits": [0, 1, 2, 3], "sampled_frame_count": 4},
        ],
        "issues": [{"target": "cyber cat"}],
    }

    plan = build_revision_plan_from_target_evaluation(
        evaluation,
        target_iteration="v3",
        patch_catalog={"cyber cat": "show one cyber cat as the foreground subject"},
        lock_catalog={"rain": "keep rain streaks visible"},
    )

    assert plan["convergence_strategy"]["repair_targets"] == ["cyber cat"]
    assert plan["convergence_strategy"]["locked_targets"] == ["rain"]
    assert plan["prompt_patches"][0]["change"] == "show one cyber cat as the foreground subject"
    assert plan["preservation_locks"][0]["lock"] == "keep rain streaks visible"


def test_report_target_comparison_uses_candidate_gate():
    source = {
        "iteration": "v1",
        "overall_score": 0.8,
        "target_scores": [
            {"target": "rain", "score": 0.9, "status": "passed"},
            {"target": "drone", "score": 0.7, "status": "weak"},
        ],
    }
    candidate = {
        "iteration": "v2",
        "overall_score": 0.7,
        "target_scores": [
            {"target": "rain", "score": 0.6, "status": "weak"},
            {"target": "drone", "score": 0.9, "status": "passed"},
        ],
    }
    plan = {
        "source_iteration": "v1",
        "target_iteration": "v2",
        "convergence_strategy": {"locked_targets": ["rain"]},
    }

    comparison = compare_report_target_evaluations(source, candidate, revision_plan=plan)

    assert comparison["candidate_status"] == "rejected"
    assert comparison["accepted_iteration"] == "v1"
    assert comparison["repaired"] == ["drone"]
    assert comparison["regressed"] == ["rain"]
