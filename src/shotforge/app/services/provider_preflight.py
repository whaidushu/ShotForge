from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request as UrlRequest, urlopen

from shotforge.app.services.provider_profiles import ProviderProfile
from shotforge.app.services.provider_workflows import ComfyUIWorkflowService


class ProviderPreflightService:
    def __init__(self, workflow_service: ComfyUIWorkflowService | None = None) -> None:
        self.workflow_service = workflow_service or ComfyUIWorkflowService()

    def preflight_provider_profile(self, profile: ProviderProfile) -> dict[str, Any]:
        checks = []

        def add(check_id: str, label: str, status: str, detail: str) -> None:
            checks.append({"check_id": check_id, "label": label, "status": status, "detail": detail})

        self._check_llm(profile, add)
        self._check_generator(profile, add)
        self._check_observer(profile, add)
        failed = len([check for check in checks if check["status"] == "failed"])
        warnings = len([check for check in checks if check["status"] == "warning"])
        return {
            "status": "failed" if failed else "warning" if warnings else "passed",
            "failed": failed,
            "warnings": warnings,
            "checks": checks,
            "profile": profile.public_dict(),
        }

    def _check_llm(self, profile: ProviderProfile, add) -> None:
        if profile.llm_provider_id == "mock":
            add(
                "llm_provider",
                "LLM provider",
                "warning",
                "Internal test LLM selected. Configure Ollama, vLLM, or OpenAI-compatible for real runs.",
            )
            return
        if not profile.llm_model:
            add("llm_model", "LLM model", "failed", "LLM model is required.")
        if profile.llm_provider_id == "openai-compatible" and not profile.llm_api_key:
            add("llm_api_key", "LLM API key", "failed", "API key is required.")
        if profile.llm_base_url:
            ok, detail = self.http_json_ok(profile.llm_base_url.rstrip("/") + "/models")
            add("llm_server", "LLM server", "passed" if ok else "warning", detail)
        else:
            add("llm_base_url", "LLM base URL", "warning", "No base URL configured.")

    def _check_generator(self, profile: ProviderProfile, add) -> None:
        if profile.generator_provider_id == "mock":
            add(
                "video_provider",
                "Video provider",
                "warning",
                "Internal test video provider selected. Configure ComfyUI for real generation.",
            )
            return
        if profile.generator_provider_id != "comfyui":
            add(
                "video_provider",
                "Video provider",
                "failed",
                f"Provider is not currently runnable: {profile.generator_provider_id}",
            )
            return
        if not profile.comfyui_base_url:
            add("comfyui_base_url", "ComfyUI base URL", "failed", "ComfyUI base URL is required.")
        else:
            ok, detail = self.http_json_ok(profile.comfyui_base_url.rstrip("/") + "/system_stats")
            add("comfyui_server", "ComfyUI server", "passed" if ok else "failed", detail)

        workflow_status = self.workflow_service.workflow_status(root=profile.comfyui_workflows_dir)
        for warning in workflow_status["warnings"]:
            add(
                warning["check_id"],
                "ComfyUI workflow discovery",
                warning["status"],
                warning["detail"],
            )
        workflows = workflow_status["workflows"]
        selected = next(
            (workflow for workflow in workflows if workflow["workflow_id"] == profile.comfyui_workflow_id),
            None,
        )
        if selected is None:
            add("comfyui_workflow", "ComfyUI workflow", "failed", "Selected workflow was not found.")
        elif not selected["callable"]:
            add("comfyui_workflow", "ComfyUI workflow", "failed", "Workflow is not API-callable.")
        else:
            add(
                "comfyui_workflow",
                "ComfyUI workflow",
                "passed",
                f"{selected['workflow_id']} / {selected['format']} / {selected['node_count']} nodes",
            )

        root = Path(profile.comfyui_workflows_dir) if profile.comfyui_workflows_dir else None
        if root and root.exists():
            add("comfyui_workflows_dir", "Workflow folder", "passed", str(root))
        elif root:
            add("comfyui_workflows_dir", "Workflow folder", "warning", f"Folder not found: {root}")

    def _check_observer(self, profile: ProviderProfile, add) -> None:
        if profile.observer_provider_id == "prompt-proxy":
            add(
                "observer_provider",
                "Visual observer",
                "warning",
                "Prompt proxy observer selected. Configure a VLM provider for real visual checks.",
            )
            return
        if profile.observer_provider_id not in {"openai-vision", "ollama-vision", "vllm-vlm"}:
            add(
                "observer_provider",
                "Visual observer",
                "failed",
                f"Unknown observer provider: {profile.observer_provider_id}",
            )
            return
        if not profile.vlm_model:
            add("vlm_model", "VLM model", "failed", "VLM model is required.")
        if profile.observer_provider_id == "openai-vision":
            if not profile.vlm_api_key:
                add("vlm_api_key", "VLM API key", "failed", "API key is required.")
            if profile.vlm_base_url:
                ok, detail = self.http_json_ok(profile.vlm_base_url.rstrip("/") + "/models")
                add("vlm_server", "VLM server", "passed" if ok else "warning", detail)
            return
        if not profile.vlm_base_url:
            add("vlm_base_url", "VLM base URL", "failed", "VLM base URL is required.")
            return
        endpoint = (
            profile.vlm_base_url.rstrip("/") + "/api/tags"
            if profile.observer_provider_id == "ollama-vision"
            else profile.vlm_base_url.rstrip("/") + "/models"
        )
        ok, detail = self.http_json_ok(endpoint)
        add("vlm_server", "VLM server", "passed" if ok else "warning", detail)

    @staticmethod
    def http_json_ok(url: str, *, timeout: float = 3.0) -> tuple[bool, str]:
        try:
            request = UrlRequest(url, method="GET")
            with urlopen(request, timeout=timeout) as response:
                return response.status < 500, f"HTTP {response.status}"
        except (OSError, URLError, TimeoutError) as exc:
            return False, str(exc)
