from shotforge.comfyui import ComfyUIArtifactResolver, build_workflow_registry
from shotforge.generators import MockGenerator, build_default_generator_registry, build_generator_catalog
from shotforge.generators.comfyui_provider import ComfyUIProvider
from shotforge.generators.open_sora_provider import OpenSoraProvider
from shotforge.llm import MockLLMProvider, build_llm_catalog
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.evaluation_workflow import run_generation


def test_mock_generator_implements_provider_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A neon train crossing a desert at sunrise", language="en")
    provider = MockGenerator()

    assert provider.provider_id == "mock"
    assert provider.display_name == "Mock Generator"
    assert provider.supports_real_generation() is False
    assert provider.capabilities().supports_video is True
    assert provider.estimate_cost(state).cost_mode == "free"


def test_generator_registry_returns_mock_provider():
    registry = build_default_generator_registry()

    assert registry.list() == ["mock"]
    assert registry.get("mock").provider_id == "mock"


def test_generator_catalog_exposes_planned_providers_without_enabling_them():
    registry = build_generator_catalog()

    assert "mock" in registry.list(available_only=False)
    assert "comfyui" in registry.list(available_only=False)
    assert "kling" in registry.list(available_only=False)
    assert registry.list() == ["mock"]
    assert registry.get("comfyui", require_available=False).supports_real_generation() is True


def test_planned_provider_classes_implement_provider_contract():
    assert ComfyUIProvider().provider_id == "comfyui"
    assert OpenSoraProvider().provider_id == "open_sora"
    assert ComfyUIProvider().supports_real_generation() is True
    assert ComfyUIProvider().capabilities().metadata["status"] == "experimental"


def test_comfyui_workflow_template_binds_prompt():
    template = build_workflow_registry().get("txt2img_sd15")
    workflow = template.bind({"prompt": "a luminous train", "negative_prompt": "blur"})

    assert workflow["2"]["inputs"]["text"] == "a luminous train"
    assert workflow["3"]["inputs"]["text"] == "blur"


def test_comfyui_artifact_resolver_extracts_outputs():
    outputs = {
        "7": {
            "images": [
                {"filename": "shotforge_00001.png", "subfolder": "", "type": "output"},
            ]
        }
    }
    artifacts = ComfyUIArtifactResolver().from_outputs(outputs)

    assert len(artifacts) == 1
    assert artifacts[0].filename == "shotforge_00001.png"


def test_llm_catalog_exposes_mock_and_planned_local_backends():
    registry = build_llm_catalog()

    assert registry.list() == ["mock"]
    assert "ollama" in registry.list(available_only=False)
    assert "vllm" in registry.list(available_only=False)
    assert MockLLMProvider().complete("hello", purpose="test").startswith("[mock:test:")


def test_run_generation_records_provider_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOTFORGE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("SHOTFORGE_VERSIONS_DIR", str(tmp_path / "versions"))
    monkeypatch.setenv("SHOTFORGE_KNOWLEDGE_BASE_PATH", str(tmp_path / "kb.json"))

    from shotforge.config import get_settings

    get_settings.cache_clear()
    state = run_design_pipeline("A neon train crossing a desert at sunrise", language="en")
    result = run_generation(state, provider_id="mock")

    assert result.provider == "mock"
    assert result.metadata["provider_id"] == "mock"
    assert result.metadata["cost_estimate"]["cost_mode"] == "free"
    assert state.metadata["generator_provider_id"] == "mock"
    assert state.metadata["generator_cost_estimate"]["estimated_cost"] == 0.0
