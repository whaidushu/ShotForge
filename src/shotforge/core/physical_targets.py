from __future__ import annotations

import re
from typing import Any

from shotforge.core.semantic_contracts import build_semantic_contract


ZH_NUMBER_WORDS = {
    "一": 1,
    "一个": 1,
    "一只": 1,
    "一台": 1,
    "两": 2,
    "两个": 2,
    "两只": 2,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
}

EN_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def extract_physical_targets(text: str, language: str = "zh") -> dict[str, Any]:
    semantic = build_semantic_contract(text, language)
    lowered = text.lower()
    targets: list[dict[str, Any]] = []

    subject = _primary_subject(text, lowered)
    if subject:
        targets.append(subject)

    targets.extend(_object_targets(text, lowered))
    targets.extend(_setting_targets(text, lowered))
    targets.extend(_atmosphere_targets(text, lowered))
    targets.extend(_action_targets(text, lowered))

    required_elements = []
    for target in targets:
        if target["type"] in {"subject", "object", "setting", "atmosphere"}:
            required_elements.append(target["label"])
    legacy = {
        "source_text": text,
        "targets": targets,
        "required_elements": _dedupe(required_elements),
        "prompt_contract": physical_contract_text(targets),
    }
    if semantic.get("targets"):
        merged_targets = _merge_targets(semantic["targets"], legacy["targets"])
        required = _dedupe([*semantic.get("required_elements", []), *legacy["required_elements"]])
        return {
            **legacy,
            **semantic,
            "targets": merged_targets,
            "required_elements": required,
            "prompt_contract": " ".join(
                part
                for part in [semantic.get("prompt_contract", ""), physical_contract_text(merged_targets)]
                if part
            ),
        }
    return legacy


def physical_contract_text(targets: list[dict[str, Any]]) -> str:
    if not targets:
        return "PHYSICAL TARGETS: keep all explicitly requested visible elements on screen."
    parts = []
    for target in targets:
        if target["type"] == "subject":
            count = target.get("count")
            count_text = f"exactly {count} " if count else ""
            parts.append(f"{count_text}{target['label']} as the primary visible subject")
        elif target["type"] == "action":
            parts.append(f"action: {target['label']}")
        else:
            parts.append(target["label"])
    return "PHYSICAL TARGETS: " + "; ".join(parts) + "."


def required_element_labels(targets_payload: dict[str, Any] | None) -> list[str]:
    if not targets_payload:
        return []
    values = targets_payload.get("required_elements", [])
    if isinstance(values, list):
        return [str(value) for value in values if str(value).strip()]
    return []


def _primary_subject(original: str, lowered: str) -> dict[str, Any] | None:
    subject_aliases = [
        ("cyber cat", ["cyber cat", "赛博猫", "賽博貓"]),
        ("cat", ["cat", "猫", "貓"]),
        ("drone", ["drone", "无人机", "無人機"]),
        ("robot", ["robot", "机器人", "機器人"]),
        ("woman", ["woman", "girl", "female protagonist", "女主", "女人"]),
        ("man", ["man", "male protagonist", "男人", "男主"]),
    ]
    for label, aliases in subject_aliases:
        if any(alias.lower() in lowered or alias in original for alias in aliases):
            return {
                "target_id": "subject_primary",
                "type": "subject",
                "label": label,
                "aliases": aliases,
                "count": _count_before_alias(original, lowered, aliases),
                "required": True,
                "visibility": "must_be_visible",
            }
    return None


def _object_targets(original: str, lowered: str) -> list[dict[str, Any]]:
    objects = [
        ("glowing drone", ["glowing drone", "发光无人机", "發光無人機", "luminous drone"]),
        ("drone", ["drone", "无人机", "無人機"]),
        ("umbrella", ["umbrella", "伞", "傘"]),
        ("train", ["train", "火车", "列车"]),
        ("cube", ["cube", "立方体"]),
    ]
    targets = []
    for label, aliases in objects:
        if label == "drone" and any(item["label"] == "glowing drone" for item in targets):
            continue
        if any(alias.lower() in lowered or alias in original for alias in aliases):
            targets.append(
                {
                    "target_id": f"object_{_slug(label)}",
                    "type": "object",
                    "label": label,
                    "aliases": aliases,
                    "required": True,
                    "visibility": "must_be_visible",
                }
            )
    return targets


def _setting_targets(original: str, lowered: str) -> list[dict[str, Any]]:
    settings = [
        ("Shanghai", ["shanghai", "上海"]),
        ("rooftop", ["rooftop", "roof top", "屋顶", "天台", "樓頂", "楼顶"]),
        ("rainy night", ["rainy night", "雨夜"]),
        ("night", ["night", "夜晚", "夜"]),
        ("rain", ["rain", "rainy", "雨"]),
        ("desert", ["desert", "沙漠"]),
    ]
    targets = []
    for label, aliases in settings:
        if label in {"night", "rain"} and any(
            item["label"] == "rainy night" for item in targets
        ):
            continue
        if any(alias.lower() in lowered or alias in original for alias in aliases):
            targets.append(
                {
                    "target_id": f"setting_{_slug(label)}",
                    "type": "setting",
                    "label": label,
                    "aliases": aliases,
                    "required": True,
                    "visibility": "must_be_visible",
                }
            )
    return targets


def _atmosphere_targets(original: str, lowered: str) -> list[dict[str, Any]]:
    targets = []
    if any(alias in original or alias in lowered for alias in ["neon", "霓虹"]):
        targets.append(
            {
                "target_id": "atmosphere_neon",
                "type": "atmosphere",
                "label": "neon glow",
                "aliases": ["neon", "霓虹"],
                "required": True,
                "visibility": "must_be_visible",
            }
        )
    return targets


def _action_targets(original: str, lowered: str) -> list[dict[str, Any]]:
    actions = [
        ("chasing", ["chases", "chasing", "pursues", "pursuing", "追逐", "追赶"]),
        ("opens", ["opens", "opening", "打开", "撑开"]),
        ("lifts", ["lifts", "lifting", "举起", "抬起"]),
    ]
    targets = []
    for label, aliases in actions:
        if any(alias.lower() in lowered or alias in original for alias in aliases):
            targets.append(
                {
                    "target_id": f"action_{_slug(label)}",
                    "type": "action",
                    "label": label,
                    "aliases": aliases,
                    "required": True,
                    "visibility": "must_be_readable",
                }
            )
    return targets


def _count_before_alias(original: str, lowered: str, aliases: list[str]) -> int | None:
    for alias in aliases:
        alias_lower = alias.lower()
        if alias_lower in lowered:
            pattern = rf"\b({'|'.join(EN_NUMBER_WORDS)}|\d+)\s+(?:\w+\s+){{0,2}}{re.escape(alias_lower)}\b"
            match = re.search(pattern, lowered)
            if match:
                value = match.group(1)
                return int(value) if value.isdigit() else EN_NUMBER_WORDS.get(value)
        if alias in original:
            for number_text, value in ZH_NUMBER_WORDS.items():
                if f"{number_text}{alias}" in original:
                    return value
    return None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _dedupe(values: list[str]) -> list[str]:
    seen = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def _merge_targets(primary: list[dict[str, Any]], secondary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = []
    seen: dict[tuple[Any, Any], dict[str, Any]] = {}
    for target in [*primary, *secondary]:
        key = (target.get("type"), target.get("label"))
        if key in seen:
            existing = seen[key]
            for field, value in target.items():
                current = existing.get(field)
                if field not in existing or current is None or current == "" or current == []:
                    existing[field] = value
            continue
        seen[key] = target
        merged.append(target)
    return merged
