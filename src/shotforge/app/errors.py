from __future__ import annotations

from typing import Any


def runtime_error_payload(exc: Exception) -> dict[str, Any]:
    message = str(exc) or exc.__class__.__name__
    lowered = message.lower()
    checks = []

    def add(check_id: str, label: str, detail: str) -> None:
        checks.append({"check_id": check_id, "label": label, "status": "failed", "detail": detail})

    if "comfyui" in lowered or "8188" in lowered or "/prompt" in lowered:
        add(
            "comfyui_server",
            "ComfyUI service",
            "ComfyUI is not reachable. Start ComfyUI and confirm the base URL, usually http://127.0.0.1:8188.",
        )
    if "ollama" in lowered or "11434" in lowered:
        add(
            "ollama_server",
            "Ollama service",
            "Ollama is not reachable. Start Ollama and confirm the base URL/model configuration.",
        )
    if "vllm" in lowered or "8000" in lowered:
        add(
            "vllm_server",
            "vLLM service",
            "vLLM is not reachable. Start the vLLM OpenAI-compatible server and confirm the configured base URL.",
        )
    if "workflow" in lowered:
        add(
            "comfyui_workflow",
            "ComfyUI workflow",
            "The selected workflow is missing or not API-callable. Search local workflows or export the workflow in API format.",
        )
    if "model" in lowered and ("not found" in lowered or "does not exist" in lowered):
        add(
            "model_name",
            "Model",
            "The configured model was not found. Check the LLM model name or ComfyUI model filenames.",
        )
    if not checks:
        add(
            "runtime",
            "Runtime service",
            "A local runtime dependency failed. Check LLM provider, video provider, workflow path, and service ports.",
        )

    return {
        "status": "failed",
        "title": "Local service is not ready",
        "message": message,
        "checks": checks,
        "exception_type": exc.__class__.__name__,
    }
