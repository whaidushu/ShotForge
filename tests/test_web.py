import re
import json
from pathlib import Path

from fastapi.testclient import TestClient

from shotforge.app.web.app import app


def assert_template_rendered(html: str) -> None:
    assert "{{" not in html
    assert "{%" not in html
    assert "%}" not in html
    assert "????" not in html
    assert "Agent ??" not in html


def test_locale_files_do_not_contain_broken_placeholders():
    locale_root = Path("src/shotforge/i18n/locales")
    broken_markers = ["????", "Agent ??", "??? API"]

    for path in locale_root.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(data, ensure_ascii=False)
        for marker in broken_markers:
            assert marker not in serialized


def test_create_run_api(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

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
            "generator_provider_id": "mock",
            "llm_provider_id": "mock",
            "llm_model": "mock",
            "evaluator_mode": "mock",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert re.match(r"^\d{8}_\d{4}(?:_\d{2})?$", payload["run_id"])
    assert "language" not in payload["state"]
    assert payload["state"]["solution_architecture"]
    assert payload["state"]["delivery_readiness"]
    assert payload["state"]["evaluation_reports"]
    assert "json" in payload["exports"]
    assert "manifest" in payload["exports"]
    assert "trace" in payload["exports"]
    assert "run_summary" in payload["exports"]
    runs = client.get("/api/runs")
    assert runs.status_code == 200
    assert any(item["run_id"] == payload["run_id"] for item in runs.json()["runs"])
    assert all("language" not in item for item in runs.json()["runs"])
    status = client.get(f"/api/runs/{payload['run_id']}/status")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    assert status.json()["total_steps"] == 5
    assert "observe" in status.json()["completed_steps"]
    package_view = client.get(f"/api/runs/{payload['run_id']}/package-view")
    assert package_view.status_code == 200
    assert "language" not in package_view.json()
    assert package_view.json()["observation"]["observation_reports"]
    package_view_export = client.get(f"/api/runs/{payload['run_id']}/export/package_view")
    assert package_view_export.status_code == 200
    assert package_view_export.json()["project_id"] == payload["project_id"]
    dashboard = client.get("/api/runs/dashboard")
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    assert dashboard_payload["total_runs"] >= 1
    assert dashboard_payload["runs"][0]["run_id"] == payload["run_id"]
    assert "language" not in dashboard_payload["runs"][0]
    assert dashboard_payload["runs"][0]["lifecycle_stage"]
    assert dashboard_payload["runs"][0]["readiness_score"] >= 0

    workbench = client.get(f"/api/runs/{payload['run_id']}/workbench")
    assert workbench.status_code == 200
    workbench_payload = workbench.json()
    assert workbench_payload["summary"]["run_id"] == payload["run_id"]
    assert workbench_payload["lifecycle"]
    assert workbench_payload["handoff_center"]["exports"]
    assert "Harness Inspector" not in json.dumps(workbench_payload, ensure_ascii=False)


def test_index_page():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert_template_rendered(response.text)
    assert "ShotForge" in response.text
    assert 'name="language"' in response.text
    assert 'id="workspace_language"' in response.text
    assert 'id="language" name="language" type="hidden"' in response.text
    assert 'value="cinematic"' in response.text
    assert 'name="llm_provider_id"' in response.text
    assert 'name="provider_profile_id"' in response.text
    assert 'name="evaluator_mode"' in response.text
    assert 'name="generator_provider_id"' in response.text
    assert 'name="observer_provider_id"' in response.text
    assert 'name="vlm_model"' in response.text
    assert 'name="comfyui_workflow_id"' in response.text
    assert 'value="comfyui"' in response.text
    assert 'value="mock"' not in response.text
    assert 'type="range"' in response.text
    assert 'id="max_iterations_value"' in response.text
    assert "window.SHOTFORGE_BOOTSTRAP" in response.text
    assert "/static/shotforge-ui.js" in response.text
    assert "const currentProviderPayload" not in response.text
    assert "工作台" in response.text
    assert "服务配置" in response.text
    assert "新建任务" in response.text
    assert "/demo?language=zh" in response.text
    assert "AI 视频生产 Agent 工作台" in response.text
    assert "服务健康" in response.text
    assert "仅设计" in response.text
    assert "New Production Run" not in response.text
    assert "Agent Video Workbench" not in response.text
    assert "Provider Health" not in response.text


def test_index_page_uses_english_when_language_is_en():
    client = TestClient(app)
    response = client.get("/?language=en")

    assert response.status_code == 200
    assert_template_rendered(response.text)
    assert "Workbench" in response.text
    assert "Providers" in response.text
    assert "New Run" in response.text
    assert "Demo" in response.text
    assert "/demo?language=en" in response.text
    assert "Agent Video Workbench" in response.text
    assert "Provider Health" in response.text


def test_demo_route_seeds_gold_sample_and_redirects(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/demo?language=en", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?run_id=shotforge_gold_sample&language=en"
    assert (tmp_path / "runs" / "shotforge_gold_sample" / "package.json").exists()

    page = client.get(response.headers["location"])
    assert page.status_code == 200
    assert_template_rendered(page.text)
    assert "hidden scanner" in page.text
    assert "shotforge_gold_sample" in page.text
    get_settings.cache_clear()


def test_chinese_demo_route_seeds_chinese_gold_sample(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/demo?language=zh", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?run_id=shotforge_gold_sample_zh&language=zh"
    assert (tmp_path / "runs" / "shotforge_gold_sample_zh" / "package.json").exists()

    page = client.get(response.headers["location"])
    assert page.status_code == 200
    assert_template_rendered(page.text)
    assert "隐藏扫描器" in page.text
    assert "shotforge_gold_sample_zh" in page.text
    get_settings.cache_clear()


def test_config_page_contains_provider_controls():
    client = TestClient(app)
    response = client.get("/config")

    assert response.status_code == 200
    assert_template_rendered(response.text)
    assert 'id="preflight_check"' in response.text
    assert 'id="test_chain"' in response.text
    assert 'id="save_provider_profile"' in response.text
    assert 'id="comfyui_search"' in response.text
    assert 'id="comfyui_search_status"' in response.text
    assert 'id="observer_provider_id"' in response.text
    assert 'id="vlm_config"' in response.text
    assert "文档" in response.text
    assert "ComfyUI" in response.text
    assert 'value="comfyui"' in response.text
    assert 'value="mock"' not in response.text
    assert "disabled" in response.text
    assert "window.SHOTFORGE_BOOTSTRAP" in response.text


def test_provider_profile_api_persists_local_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/provider-profiles",
        json={
            "profile_id": "local-comfy",
            "name": "Local ComfyUI",
            "llm_provider_id": "ollama",
            "llm_model": "local-chat-model",
            "llm_base_url": "http://localhost:11434/v1",
            "generator_provider_id": "comfyui",
            "comfyui_base_url": "http://127.0.0.1:8001",
            "comfyui_workflows_dir": str(tmp_path),
            "comfyui_workflow_id": "wan2_2_i2v_empty_start",
            "observer_provider_id": "ollama-vision",
            "vlm_model": "local-vision-model",
            "vlm_base_url": "http://localhost:11434",
            "vlm_api_key": "secret",
            "vlm_frame_sample_count": 5,
            "vlm_confidence_threshold": 0.7,
            "vlm_require_json": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["profile"]["profile_id"] == "local-comfy"
    profiles = client.get("/api/provider-profiles")
    assert profiles.status_code == 200
    assert profiles.json()["profiles"][0]["name"] == "Local ComfyUI"
    assert profiles.json()["profiles"][0]["llm_api_key"] == ""
    assert profiles.json()["profiles"][0]["observer_provider_id"] == "ollama-vision"
    assert profiles.json()["profiles"][0]["vlm_model"] == "local-vision-model"
    assert profiles.json()["profiles"][0]["vlm_api_key"] == ""
    assert profiles.json()["profiles"][0]["has_vlm_api_key"] is True
    get_settings.cache_clear()


def test_preflight_api_marks_internal_test_profile_as_not_deployment_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/preflight",
        json={
            "provider_profile_id": "mock",
            "provider_profile_name": "Mock",
            "llm_provider_id": "mock",
            "generator_provider_id": "mock",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "warning"
    assert payload["failed"] == 0
    assert any(check["check_id"] == "video_provider" for check in payload["checks"])
    assert any(check["check_id"] == "observer_provider" for check in payload["checks"])
    get_settings.cache_clear()


def test_internal_test_chain_api_runs_smoke_test(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post("/api/test-chain")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "passed"
    assert payload["run_id"]
    assert payload["run_url"].startswith("/?run_id=")
    get_settings.cache_clear()


def test_capability_catalog_api():
    client = TestClient(app)
    response = client.get("/api/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["agents"]["specs"]
    assert payload["agents"]["dependency_edges"]
    assert payload["agent_harness"]["state_management"] == "ProjectState"
    assert "knowledge.search" in payload["infra"]["mcp"]
    assert "manifest" in payload["export_formats"]
    assert "GET /api/runs/{run_id}/readiness" in payload["api_routes"]
    assert any(item["provider_id"] == "mock" for item in payload["generator_providers"])
    assert any(item["playbook_id"] == "media_advertising_video_ops" for item in payload["playbooks"])


def test_observer_provider_catalog_api():
    client = TestClient(app)
    response = client.get("/api/observer-providers")

    assert response.status_code == 200
    payload = response.json()
    provider_ids = {item["provider_id"] for item in payload["observer_providers"]}
    assert {"prompt-proxy", "ollama-vision", "vllm-vlm", "openai-vision"}.issubset(provider_ids)


def test_comfyui_workflows_api():
    client = TestClient(app)
    response = client.get("/api/comfyui/workflows")

    assert response.status_code == 200
    payload = response.json()
    assert "enabled" in payload
    assert "base_url" in payload
    assert payload["workflows_dir"]
    assert any(item["workflow_id"] == "wan2_2_i2v_empty_start" for item in payload["workflows"])


def test_comfyui_workflows_api_searches_local_root(tmp_path):
    workflow = tmp_path / "my_video_workflow.json"
    workflow.write_text(
        json.dumps({"1": {"class_type": "PreviewAny", "inputs": {"source": "{{prompt}}"}}}),
        encoding="utf-8",
    )

    client = TestClient(app)
    response = client.get("/api/comfyui/workflows", params={"root": str(tmp_path)})

    assert response.status_code == 200
    workflows = response.json()["workflows"]
    assert any(item["workflow_id"] == "local:my_video_workflow" for item in workflows)


def test_comfyui_workflow_api_reports_missing_folder():
    client = TestClient(app)
    response = client.get("/api/comfyui/workflows", params={"root": "Z:/path/that/does/not/exist"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["warnings"]
    assert payload["warnings"][0]["check_id"] == "comfyui_workflows_dir"


def test_health_api():
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "runs_dir_exists" in payload["storage"]
    assert payload["comfyui"]["workflow_id"]
    assert payload["observer"]["provider"]


def test_create_run_form_redirects(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
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
            "generator_provider_id": "mock",
            "llm_provider_id": "mock",
            "llm_model": "mock",
            "llm_base_url": "",
            "llm_api_key": "",
            "evaluator_mode": "mock",
            "observer_provider_id": "prompt-proxy",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert re.match(r"^/\?run_id=\d{8}_\d{4}(?:_\d{2})?$", response.headers["location"])
    get_settings.cache_clear()


def test_create_run_form_reports_runtime_service_errors(monkeypatch):
    from shotforge.app.web import app as web_app

    def fail_create_run(**kwargs):
        raise ConnectionRefusedError("ComfyUI http://127.0.0.1:8188 /prompt refused")

    monkeypatch.setattr(web_app.run_service, "create_run", fail_create_run)
    client = TestClient(app)
    response = client.post(
        "/runs",
        data={
            "idea": "A local runtime failure should render as an actionable banner",
            "style": "cinematic",
            "language": "en",
            "duration_seconds": "8",
            "mode": "full_loop",
            "rubric_id": "baseline_v1",
            "generator_provider_id": "comfyui",
            "llm_provider_id": "ollama",
            "llm_model": "local-chat-model",
            "llm_base_url": "",
            "llm_api_key": "",
            "evaluator_mode": "llm",
            "comfyui_base_url": "http://127.0.0.1:8188",
            "comfyui_workflows_dir": "",
            "comfyui_workflow_id": "wan2_2_i2v_empty_start",
            "comfyui_width": "320",
            "comfyui_height": "320",
            "comfyui_length": "9",
            "comfyui_fps": "8",
            "comfyui_max_shots": "0",
        },
    )

    assert response.status_code == 503
    assert_template_rendered(response.text)
    assert "Local service is not ready" in response.text
    assert "ComfyUI is not reachable" in response.text


def test_create_run_api_reports_runtime_service_errors(monkeypatch):
    from shotforge.app.web import app as web_app

    def fail_create_run_from_payload(payload):
        raise ConnectionRefusedError("Ollama http://localhost:11434/v1 refused")

    monkeypatch.setattr(web_app.run_service, "create_run_from_payload", fail_create_run_from_payload)
    client = TestClient(app)
    response = client.post(
        "/api/runs",
        json={
            "idea": "A local runtime failure should be structured",
            "duration_seconds": 8,
            "language": "en",
            "with_evaluation": True,
            "generator_provider_id": "mock",
            "llm_provider_id": "ollama",
            "llm_model": "local-chat-model",
            "evaluator_mode": "llm",
        },
    )

    assert response.status_code == 503
    payload = response.json()["detail"]
    assert payload["status"] == "failed"
    assert any(check["check_id"] == "ollama_server" for check in payload["checks"])


def test_create_run_form_records_provider_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/runs",
        data={
            "idea": "A local provider configuration check",
            "style": "cinematic",
            "language": "en",
            "duration_seconds": "24",
            "mode": "design",
            "rubric_id": "baseline_v1",
            "generator_provider_id": "mock",
            "llm_provider_id": "mock",
            "llm_model": "mock",
            "llm_base_url": "",
            "llm_api_key": "",
            "evaluator_mode": "mock",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    run_id = response.headers["location"].split("run_id=", 1)[1]
    state = client.get(f"/api/runs/{run_id}").json()
    assert state["metadata"]["llm_provider_id"] == "mock"
    assert state["metadata"]["llm_model"] == "mock"
    assert state["metadata"]["generator_provider_id"] == "mock"
    assert state["metadata"]["observer_provider_id"] == "prompt-proxy"
    status = client.get(f"/api/runs/{run_id}/status")
    assert status.status_code == 200
    assert status.json()["mode"] == "design"
    assert status.json()["total_steps"] == 2

    page = client.get(f"/?run_id={run_id}&language=en")
    assert page.status_code == 200
    assert re.search(r">\s*100%\s*<", page.text)
    get_settings.cache_clear()


def test_create_run_api_with_planning(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

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
            "llm_provider_id": "mock",
            "llm_model": "mock",
            "evaluator_mode": "mock",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert 2 <= payload["state"]["version"] <= 5
    assert payload["state"]["correction_plans"]
    assert payload["state"]["correction_patches"]
    assert payload["state"]["version_diffs"]
    assert payload["state"]["score_deltas"]
    assert payload["state"]["regression_checks"]
    assert payload["state"]["verification_reports"]
    assert payload["state"]["convergence_steps"]
    assert 1 <= len(payload["state"]["convergence_steps"]) <= 4
    assert payload["state"]["convergence_steps"][-1]["stop_reason"] in {
        "design_package_unchanged",
        "selected_iterations_reached",
        "all_tracked_issues_resolved",
    }
    assert payload["state"]["metadata"]["generator_provider_id"] == "mock"
    assert payload["state"]["metadata"]["next_version_preview"]["next_version"] >= 2
    status = client.get(f"/api/runs/{payload['run_id']}/status")
    assert status.status_code == 200
    assert status.json()["total_steps"] == 6

    page = client.get(f"/?run_id={payload['run_id']}&language=en")
    assert page.status_code == 200
    assert_template_rendered(page.text)
    assert "Version Chain" in page.text
    assert "Solution Architecture" in page.text
    assert "Acceptance criteria" in page.text
    assert "Delivery Readiness" in page.text
    assert "Handoff" in page.text
    assert "Manifest" in page.text
    assert "Run Summary" in page.text
    assert "View diff" in page.text
    assert "Production package unchanged" in page.text
    assert "Run Details" in page.text
    assert "Connected tools" in page.text
    assert "Execution limits" in page.text
    assert "Reference memory" in page.text
    assert "State changes" in page.text
    assert "Validation status" in page.text
    assert "Workflow map" in page.text
    assert "Harness Inspector" not in page.text
    assert "Transform production state" in page.text

    versions = client.get(f"/api/runs/{payload['run_id']}/versions")
    assert versions.status_code == 200
    assert versions.json()
    assert any(item["label"].startswith("redesign_iter") for item in versions.json())

    evidence = client.get(f"/api/runs/{payload['run_id']}/runtime-evidence")
    assert evidence.status_code == 200
    audit = evidence.json()
    assert audit["run_id"] == payload["run_id"]
    assert audit["contexts"]
    assert audit["tool_calls"]
    assert audit["state_transitions"]
    assert audit["state_summary"]["state_transitions"] >= 1
    assert audit["agent_topology"]["nodes"]
    assert audit["agent_topology"]["edges"]
    assert "knowledge.search" in audit["policies"]["mcp_tool_names"]
    assert audit["solution"]["knowledge_assets"]
    assert audit["readiness"]["checks"]

    harness = client.get(f"/api/runs/{payload['run_id']}/harness")
    assert harness.status_code == 200
    assert harness.json()["run_id"] == payload["run_id"]

    manifest = client.get(f"/api/runs/{payload['run_id']}/export/manifest")
    assert manifest.status_code == 200
    assert manifest.json()["run_id"] == payload["run_id"]

    readiness = client.get(f"/api/runs/{payload['run_id']}/readiness")
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["run_id"] == payload["run_id"]
    assert readiness_payload["checks"]
    assert readiness_payload["summary"]["warnings"] >= 0


def test_chinese_planning_page_has_no_broken_placeholders(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/runs",
        json={
            "idea": "一只赛博猫在雨夜上海屋顶追逐发光无人机",
            "duration_seconds": 24,
            "language": "zh",
            "with_planning": True,
            "generator_provider_id": "mock",
            "llm_provider_id": "mock",
            "llm_model": "mock",
            "evaluator_mode": "mock",
        },
    )
    assert response.status_code == 200
    page = client.get(f"/?run_id={response.json()['run_id']}&language=zh")

    assert page.status_code == 200
    assert_template_rendered(page.text)
    assert "解决方案架构" in page.text
    assert "交付就绪度" in page.text
    assert "状态变化" in page.text
    assert "任务包视图" in page.text
    assert "交付中心" in page.text
    assert "迭代时间线" in page.text
    assert "Run Overview" not in page.text
    assert "Provider Health" not in page.text
    assert "Iteration Timeline" not in page.text
    assert "Handoff Center" not in page.text
    assert "Package View" not in page.text


def test_generation_artifact_api_and_web_links(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings
    from shotforge.exporters import ExportManager
    from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline

    get_settings.cache_clear()
    state = run_full_loop_pipeline(
        "A five second repair demo",
        language="en",
        generator_provider_id="mock",
    )
    run_root = Path(get_settings().runs_dir) / state.run_id
    artifact_root = run_root / "iterations" / "v001"
    video_path = artifact_root / "videos" / "v001_shot_01_hook.mp4"
    prompt_path = artifact_root / "prompts" / "v001_shot_01_hook.txt"
    prompt_json_path = artifact_root / "prompts" / "v001_shot_01_hook.json"
    workflow_path = artifact_root / "workflows" / "v001_shot_01_hook.api.json"
    for path in [video_path, prompt_path, prompt_json_path, workflow_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(b"fake mp4")
    prompt_path.write_text("prompt", encoding="utf-8")
    prompt_json_path.write_text("{}", encoding="utf-8")
    workflow_path.write_text("{}", encoding="utf-8")

    shot = state.generation_results[0].shots[0]
    shot.mock_video_uri = str(video_path)
    shot.metadata.update(
        {
            "iteration": "v001",
            "artifact_path": str(video_path),
            "prompt_text_path": str(prompt_path),
            "prompt_json_path": str(prompt_json_path),
            "workflow_api_path": str(workflow_path),
            "local_filename": video_path.name,
        }
    )
    ExportManager().export_all(state)

    client = TestClient(app)
    artifacts = client.get(f"/api/runs/{state.run_id}/generation-artifacts")
    assert artifacts.status_code == 200
    payload = artifacts.json()
    assert payload[0]["video_filename"] == "v001_shot_01_hook.mp4"
    assert payload[0]["video_url"].endswith("/api/runs/" + state.run_id + "/artifacts/video/v001/shot_01")

    video = client.get(f"/api/runs/{state.run_id}/artifacts/video/v001/shot_01")
    assert video.status_code == 200
    assert video.content == b"fake mp4"

    page = client.get(f"/?run_id={state.run_id}&language=en")
    assert page.status_code == 200
    assert_template_rendered(page.text)
    assert "Generated Artifacts" in page.text
    assert "v001_shot_01_hook.mp4" in page.text


def test_create_run_api_rejects_unknown_generator_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_PROVIDER_PROFILES_PATH", str(tmp_path / "profiles.json"))

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
            "generator_provider_id": "unknown-provider",
        },
    )

    assert response.status_code == 400
    assert "Unknown generator provider" in response.json()["detail"]
    assert not (tmp_path / "profiles.json").exists()
    get_settings.cache_clear()
