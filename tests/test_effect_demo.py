from pathlib import Path

from fastapi.testclient import TestClient

from shotforge.workflows.effect_demo_workflow import load_effect_comparison, run_effect_demo


def _isolate_runtime(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()


def test_effect_demo_generates_v1_v2_v3_convergence(tmp_path, monkeypatch):
    _isolate_runtime(tmp_path, monkeypatch)

    state = run_effect_demo("cyber_cat_rooftop", language="en", generator_provider_id="mock")

    effect = state.metadata["effect_demo"]
    comparison = effect["comparison"]
    assert state.metadata["run_mode"] == "effect_demo"
    assert len(state.shots) == 1
    assert state.shots[0].duration_seconds == 5
    assert len(state.generation_results) == 3
    assert comparison["case_id"] == "cyber_cat_rooftop"
    assert comparison["v2_score"] >= comparison["v1_score"]
    assert comparison["v3_score"] >= comparison["v2_score"]
    assert comparison["structured_delta"] >= 0
    assert comparison["compensation_delta"] >= 0
    assert comparison["target_changes"]
    assert comparison["revision_plan"]["prompt_patches"]
    assert comparison["revision_plan"]["source_iteration"] == "v2"
    assert comparison["revision_plan"]["target_iteration"] == "v3"
    assert "convergence_strategy" in comparison["revision_plan"]
    assert "preservation_locks" in comparison["revision_plan"]
    assert "regressed" in comparison
    assert comparison["candidate_status"] in {"accepted", "rejected"}
    assert comparison["accepted_iteration"] in {"v2", "v3"}
    assert state.generation_results[0].shots[0].metadata["iteration"] == "v001"
    assert state.generation_results[1].shots[0].metadata["iteration"] == "v002"
    assert state.generation_results[2].shots[0].metadata["iteration"] == "v003"
    assert state.version == 3
    assert "PHYSICAL TARGETS" in state.prompt_package.prompts[0].prompt

    for path in effect["paths"].values():
        assert Path(path).exists()

    loaded = load_effect_comparison(state.run_id)
    assert loaded["score_delta"] == comparison["score_delta"]
    assert loaded["v3_score"] == comparison["v3_score"]


def test_effect_demo_api_creates_case_run(tmp_path, monkeypatch):
    _isolate_runtime(tmp_path, monkeypatch)

    from shotforge.app.web.app import app

    client = TestClient(app)
    response = client.post(
        "/api/effect-demos/cyber_cat_rooftop",
        json={"language": "en", "generator_provider_id": "mock"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "cyber_cat_rooftop"
    assert payload["comparison"]["target_changes"]
    assert payload["comparison"]["v3_score"] >= payload["comparison"]["v2_score"]
    run_id = payload["run_id"]

    comparison = client.get(f"/api/runs/{run_id}/effect-comparison")
    assert comparison.status_code == 200
    assert comparison.json()["case_id"] == "cyber_cat_rooftop"

    page = client.get(f"/runs/{run_id}/effect-comparison?language=en")
    assert page.status_code == 200
    assert "Effect Demo" in page.text
    assert "Target Changes" in page.text
