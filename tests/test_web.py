import re

from fastapi.testclient import TestClient

from shotforge.app.web.app import app


def test_create_run_api(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/runs",
        json={
            "idea": "A neon train crossing a desert at sunrise",
            "duration_seconds": 24,
            "language": "en",
            "with_evaluation": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert re.match(r"^\d{8}_\d{4}(?:_\d{2})?$", payload["run_id"])
    assert payload["state"]["language"] == "en"
    assert payload["state"]["evaluation_reports"]
    assert "json" in payload["exports"]


def test_index_page():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "ShotForge" in response.text
    assert 'name="language"' in response.text
    assert 'name="generator_provider_id"' in response.text
    assert 'value="mock"' in response.text
    assert 'value="comfyui"' in response.text
    assert "disabled" in response.text
    assert 'type="range"' in response.text
    assert 'id="max_iterations_value"' in response.text
    assert "show-signals" in response.text
    assert "创建任务包" in response.text
    assert "仅设计" in response.text


def test_create_run_form_redirects():
    client = TestClient(app)
    response = client.post(
        "/runs",
        data={
            "idea": "一只赛博猫在雨夜上海屋顶追逐发光无人机",
            "style": "cinematic",
            "language": "zh",
            "duration_seconds": "24",
            "mode": "full_loop",
            "rubric_id": "baseline_v1",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert re.match(r"^/\?run_id=\d{8}_\d{4}(?:_\d{2})?$", response.headers["location"])


def test_create_run_api_with_planning(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/runs",
        json={
            "idea": "A neon train crossing a desert at sunrise",
            "duration_seconds": 24,
            "language": "en",
            "with_planning": True,
            "max_iterations": 4,
            "generator_provider_id": "mock",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"]["version"] == 3
    assert payload["state"]["correction_plans"]
    assert payload["state"]["correction_patches"]
    assert payload["state"]["version_diffs"]
    assert payload["state"]["score_deltas"]
    assert payload["state"]["regression_checks"]
    assert payload["state"]["verification_reports"]
    assert payload["state"]["convergence_steps"]
    assert len(payload["state"]["convergence_steps"]) == 2
    assert payload["state"]["convergence_steps"][-1]["stop_reason"] == "design_package_unchanged"
    assert payload["state"]["metadata"]["generator_provider_id"] == "mock"
    assert payload["state"]["metadata"]["next_version_preview"]["next_version"] >= 2

    page = client.get(f"/?run_id={payload['run_id']}&language=en")
    assert page.status_code == 200
    assert "Version Chain" in page.text
    assert "View diff" in page.text
    assert "Production package unchanged" in page.text
    assert "Harness Inspector" in page.text
    assert "Tool Calls" in page.text
    assert "Execution Policy" in page.text
    assert "MCP Tools" in page.text
    assert "Sandbox" in page.text

    versions = client.get(f"/api/runs/{payload['run_id']}/versions")
    assert versions.status_code == 200
    assert versions.json()
    assert any(item["label"].startswith("redesign_iter") for item in versions.json())


def test_create_run_api_rejects_unknown_generator_provider():
    client = TestClient(app)
    response = client.post(
        "/api/runs",
        json={
            "idea": "A neon train crossing a desert at sunrise",
            "duration_seconds": 24,
            "language": "en",
            "with_evaluation": True,
            "generator_provider_id": "unknown-provider",
        },
    )

    assert response.status_code == 400
    assert "Unknown generator provider" in response.json()["detail"]
