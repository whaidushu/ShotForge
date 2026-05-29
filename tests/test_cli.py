from typer.testing import CliRunner

from shotforge.app.cli.main import app
from shotforge.workflows.design_workflow import run_design_pipeline


def test_cli_audit_prints_harness_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A neon train crossing a desert at sunrise", language="en")
    package_json = next(item.path for item in state.exports if item.format == "json")

    result = CliRunner().invoke(app, ["audit", package_json])

    assert result.exit_code == 0
    assert "ShotForge Harness Audit" in result.output
    assert "Agent Contexts" in result.output
    assert "Tool Calls" in result.output
    assert "State Transitions" in result.output
    assert "Transform production state" in result.output
    assert "knowledge.search" in result.output
    assert "media_advertising_video_ops" in result.output


def test_cli_capabilities_prints_catalog():
    result = CliRunner().invoke(app, ["capabilities"])

    assert result.exit_code == 0
    assert "ShotForge Capability Catalog" in result.output
    assert "Generator Providers" in result.output
    assert "GET /api/runs/{run_id}/harness" in result.output


def test_cli_doctor_prints_settings():
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "ShotForge Doctor" in result.output
    assert "runs_dir" in result.output
    assert "memory_store_path" in result.output
