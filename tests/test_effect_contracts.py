from shotforge.core.effect_contract import build_effect_contract
from shotforge.core.effect_matrix import build_effect_target_matrix, matrix_to_revision_input
from shotforge.core.physical_convergence import build_revision_plan_from_target_evaluation
from shotforge.core.physical_targets import extract_physical_targets
from shotforge.workflows.design_workflow import run_design_pipeline


def test_effect_contract_normalizes_physical_targets_and_reserves_controls():
    payload = extract_physical_targets(
        "A robot dog chases a glowing drone across a rooftop",
        "en",
    )
    contract = build_effect_contract(
        payload,
        source_text="A robot dog chases a glowing drone across a rooftop",
        creative_controls=[
            {
                "control_id": "cinematic_intensity",
                "label": "cinematic intensity",
                "value": 0.7,
                "intent": "reserve UI creative control mapping",
            }
        ],
    )

    labels = {target.label for target in contract.targets}
    target_types = {target.target_type for target in contract.targets}

    assert "robot dog" in labels
    assert "glowing drone" in labels
    assert "rooftop" in labels
    assert target_types.issubset(
        {
            "entity_presence",
            "entity_attribute",
            "count_constraint",
            "spatial_relation",
            "action_legibility",
        }
    )
    assert contract.creative_controls[0].control_id == "cinematic_intensity"
    assert all(target.shot_id == "shot_001" for target in contract.targets)


def test_design_pipeline_extracts_effect_contract_before_prompt_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline(
        "A robot dog chases a glowing drone across a rooftop",
        duration_seconds=8,
        language="en",
    )
    prompt = state.prompt_package.prompts[0]
    labels = {target["label"] for target in state.metadata["effect_contract"]["targets"]}

    assert {"robot dog", "glowing drone", "rooftop"}.issubset(labels)
    assert state.metadata["effect_contract_stage"] == "intent_contract_extraction"
    assert prompt.parameters["effect_contract_id"] == state.metadata["effect_contract"]["contract_id"]
    assert "EFFECT CONTRACT" in prompt.prompt
    assert any("entity_presence.glowing_drone" in item for item in prompt.structured_template.physical_constraints)
    get_settings.cache_clear()


def test_effect_target_matrix_adds_failure_reason_and_repair_suggestion():
    payload = extract_physical_targets(
        "A robot dog chases a glowing drone across a rooftop",
        "en",
    )
    contract = build_effect_contract(payload)
    evaluation = {
        "iteration": "v2",
        "overall_score": 0.5,
        "visual_observation_available": True,
        "target_scores": [
            {
                "target": "robot dog",
                "score": 0.9,
                "visual_score": 1.0,
                "prompt_score": 1.0,
                "frame_hits": [0, 1],
                "sampled_frame_count": 2,
                "generated_hit": True,
                "prompt_hit": True,
                "status": "passed",
            },
            {
                "target": "glowing drone",
                "score": 0.35,
                "visual_score": 0.0,
                "prompt_score": 0.8,
                "frame_hits": [],
                "sampled_frame_count": 2,
                "generated_hit": False,
                "prompt_hit": True,
                "status": "failed",
            },
        ],
    }

    matrix = build_effect_target_matrix(contract, evaluation)
    drone = next(row for row in matrix.target_scores if row.target == "glowing drone")
    robot_dog = next(row for row in matrix.target_scores if row.target == "robot dog")

    assert drone.failure_reason == "model_ignored"
    assert "glowing drone" in drone.repair_suggestion
    assert robot_dog.locked is True
    assert "robot dog" in matrix.locked_targets


def test_revision_plan_consumes_target_matrix_rows():
    payload = extract_physical_targets(
        "A robot dog chases a glowing drone across a rooftop",
        "en",
    )
    contract = build_effect_contract(payload)
    matrix = build_effect_target_matrix(
        contract,
        {
            "iteration": "v2",
            "overall_score": 0.7,
            "visual_observation_available": True,
            "target_scores": [
                {
                    "target": "robot dog",
                    "score": 0.92,
                    "frame_hits": [0, 1, 2],
                    "sampled_frame_count": 3,
                    "generated_hit": True,
                    "prompt_hit": True,
                    "status": "passed",
                },
                {
                    "target": "glowing drone",
                    "score": 0.36,
                    "frame_hits": [],
                    "sampled_frame_count": 3,
                    "generated_hit": False,
                    "prompt_hit": True,
                    "status": "failed",
                },
            ],
        },
    )

    plan = build_revision_plan_from_target_evaluation(
        matrix_to_revision_input(matrix),
        target_iteration="v3",
    )

    assert plan["convergence_strategy"]["target_matrix_available"] is True
    assert plan["convergence_strategy"]["repair_targets"] == ["glowing drone"]
    assert plan["convergence_strategy"]["locked_targets"] == ["robot dog"]
    assert plan["prompt_patches"][0]["failure_reason"] == "model_ignored"


def test_target_matrix_prefers_vlm_target_checks():
    payload = extract_physical_targets(
        "A robot dog chases a glowing drone across a rooftop",
        "en",
    )
    contract = build_effect_contract(payload)
    matrix = build_effect_target_matrix(
        contract,
        {
            "iteration": "v2",
            "overall_score": 0.8,
            "visual_observation_available": True,
            "frame_observations": [
                {
                    "target_checks": [
                        {
                            "target_id": "entity_presence.glowing_drone",
                            "label": "glowing drone",
                            "target_type": "entity_presence",
                            "visible": False,
                            "score": 0.2,
                            "evidence": "No drone is physically visible.",
                            "failure_reason": "model_ignored",
                            "suggested_repair": "separate the glowing drone from background neon",
                        }
                    ]
                },
                {
                    "target_checks": [
                        {
                            "target_id": "entity_presence.glowing_drone",
                            "label": "glowing drone",
                            "target_type": "entity_presence",
                            "visible": True,
                            "score": 0.65,
                            "evidence": "A small drone-like light is visible.",
                            "failure_reason": "prompt_weak",
                            "suggested_repair": "make the drone silhouette larger",
                        }
                    ]
                },
            ],
            "target_scores": [
                {
                    "target": "glowing drone",
                    "score": 0.9,
                    "visual_score": 0.9,
                    "prompt_score": 1.0,
                    "frame_hits": [0, 1],
                    "sampled_frame_count": 2,
                    "generated_hit": True,
                    "prompt_hit": True,
                    "status": "passed",
                }
            ],
        },
    )

    drone = next(row for row in matrix.target_scores if row.target == "glowing drone")

    assert drone.score == 0.425
    assert drone.status == "failed"
    assert drone.failure_reason == "model_ignored"
    assert drone.frame_hits == [1]
    assert "No drone is physically visible." in drone.evidence
