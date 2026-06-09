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
        "options": {"temperature": 0, "num_predict": 512},
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
    content = str(message.get("content") or message.get("thinking") or "{}")
    return _observation_payload(content, context)


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
    required = context.get("required_elements") or []
    required_text = ", ".join(str(item) for item in required)
    return (
        "/no_think\n"
        "Return JSON only. Inspect visible physical video content, not captions or text labels. "
        f"Required targets: {required_text}. "
        "Use this schema exactly: "
        "{\"detected_elements\":[],\"face_identity\":\"\",\"action_summary\":\"\","
        "\"style_summary\":\"\",\"color_summary\":\"\",\"confidence\":0,\"evidence\":\"\"}. "
        "Only include required targets in detected_elements when physically visible; list missing "
        f"targets in evidence. Shot={context.get('shot_id','')}."
    )


def _observation_payload(content: str, context: dict[str, Any]) -> dict[str, Any]:
    data = _loads_json_object(content)
    if not data:
        data = _fallback_observation_from_text(content, context)
    elements = data.get("detected_elements", [])
    if not isinstance(elements, list):
        elements = []
    return {
        "detected_elements": [str(item) for item in elements[:12]],
        "face_identity": _string_or_empty(data.get("face_identity")),
        "action_summary": _string_or_empty(data.get("action_summary")),
        "style_summary": _string_or_empty(data.get("style_summary")),
        "color_summary": _string_or_empty(data.get("color_summary")),
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


def _fallback_observation_from_text(content: str, context: dict[str, Any]) -> dict[str, Any]:
    text = content.strip()
    lowered = text.lower()
    detected = []
    missing = []
    for target in context.get("required_elements", []) or []:
        target_text = str(target)
        target_lower = target_text.lower()
        target_context = _target_context(lowered, target_lower)
        if not target_context:
            missing.append(target_text)
            continue
        window = target_context
        if any(
            marker in window
            for marker in [
                "not visible",
                "not present",
                "not shown",
                "no actual",
                "no visible",
                "absent",
                "missing",
                "text only",
            ]
        ):
            missing.append(target_text)
            continue
        if any(marker in window for marker in ["visible", "present", "shown", "seen", "appears"]):
            detected.append(target_text)
    if not text:
        evidence = "No VLM text returned."
    else:
        evidence = text[:1200]
    if missing and len(missing) == len(context.get("required_elements", []) or []):
        confidence = 0.35
    else:
        confidence = 0.45 if detected else 0.2
    return {
        "detected_elements": detected,
        "face_identity": "",
        "action_summary": "",
        "style_summary": "",
        "color_summary": "",
        "confidence": confidence,
        "evidence": evidence,
    }


def _target_context(text: str, target: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")) and stripped[2:].startswith(target):
            return stripped
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(target):
            return stripped
    index = text.find(target)
    if index < 0:
        return ""
    return text[max(0, index - 24) : index + len(target) + 160]


def _string_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


def _clamp_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(parsed, 0.0), 1.0)
