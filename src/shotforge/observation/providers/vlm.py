from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request as UrlRequest, urlopen

def describe_frame_with_openai_compatible(
    frame_path: Path,
    context: dict[str, Any],
    *,
    model: str,
    base_url: str = "",
    api_key: str = "",
    require_json: bool = True,
    timeout_seconds: float = 90.0,
) -> dict[str, Any]:
    if not model:
        raise RuntimeError("SHOTFORGE_VLM_MODEL is required for VLM observation.")
    if not api_key:
        raise RuntimeError("SHOTFORGE_VLM_API_KEY is required for OpenAI-compatible vision.")
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=timeout_seconds)
    kwargs = {"response_format": {"type": "json_object"}} if require_json else {}
    response = client.chat.completions.create(
        model=model,
        messages=_vision_messages(frame_path, context),
        temperature=0,
        **kwargs,
    )
    return _observation_payload(response.choices[0].message.content or "{}", context)


def describe_frame_with_ollama(
    frame_path: Path,
    context: dict[str, Any],
    *,
    model: str,
    base_url: str,
    timeout_seconds: float = 90.0,
) -> dict[str, Any]:
    if not model:
        raise RuntimeError("SHOTFORGE_VLM_MODEL is required for Ollama vision.")
    image_b64 = base64.b64encode(frame_path.read_bytes()).decode("ascii")
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {
                "role": "user",
                "content": _observer_prompt(context),
                "images": [image_b64],
            }
        ],
    }
    url = base_url.rstrip("/") + "/api/chat"
    request = UrlRequest(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Ollama vision request failed: {exc}") from exc
    message = data.get("message", {}) if isinstance(data, dict) else {}
    return _observation_payload(str(message.get("content", "{}")), context)


def _vision_messages(frame_path: Path, context: dict[str, Any]) -> list[dict[str, Any]]:
    image_b64 = base64.b64encode(frame_path.read_bytes()).decode("ascii")
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": _observer_prompt(context)},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ],
        }
    ]


def _observer_prompt(context: dict[str, Any]) -> str:
    return (
        "Analyze this generated video frame for ShotForge evaluation. "
        "Return one JSON object only with keys: detected_elements as short strings, "
        "face_identity, action_summary, style_summary, color_summary, confidence from 0 to 1, "
        "and evidence. Focus on visible physical objects, countable subjects, location, weather, "
        "and action continuity. "
        f"Context: project={context.get('project_id','')} shot={context.get('shot_id','')}."
    )


def _observation_payload(content: str, context: dict[str, Any]) -> dict[str, Any]:
    data = _loads_json_object(content)
    elements = data.get("detected_elements", [])
    if not isinstance(elements, list):
        elements = []
    return {
        "detected_elements": [str(item) for item in elements[:12]],
        "face_identity": str(data.get("face_identity", "")),
        "action_summary": str(data.get("action_summary", "")),
        "style_summary": str(data.get("style_summary", "")),
        "color_summary": str(data.get("color_summary", "")),
        "confidence": _clamp_float(data.get("confidence", 0.0)),
        "metadata": {
            "provider_id": context.get("provider_id", ""),
            "evidence": data.get("evidence", ""),
            "vlm_raw": data,
        },
    }


def _loads_json_object(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(content[start : end + 1])
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}


def _clamp_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(parsed, 0.0), 1.0)
