from __future__ import annotations

from typing import Any
import re


ENTITY_MODIFIERS = [
    {
        "id": "cyber",
        "labels": ["cyber", "cybernetic", "赛博"],
        "traits": [
            "visible cybernetic or mechanical details attached to the subject",
            "metallic panels, LED seams, glowing collar, robotic joints, or synthetic body surfaces",
        ],
        "negative": "ordinary biological subject without cybernetic details",
    },
    {
        "id": "robot",
        "labels": ["robot", "robotic", "machine", "机器", "机械"],
        "traits": [
            "visible mechanical construction attached to the subject",
            "metal limbs, articulated joints, panels, sensors, or robotic silhouette",
        ],
        "negative": "ordinary animal or person without machine traits",
    },
    {
        "id": "bread",
        "labels": ["bread", "toast", "面包", "吐司"],
        "traits": [
            "bread material is part of the character identity",
            "visible crust, crumb texture, toasted surface, or pastry-like body shape",
        ],
        "negative": "ordinary person holding bread or separate bread prop",
    },
    {
        "id": "glowing",
        "labels": ["glowing", "luminous", "发光"],
        "traits": ["visible emitted light attached to the object"],
        "negative": "non-glowing object",
    },
]


ENTITY_HEADS = [
    {"id": "cat", "labels": ["cat", "猫"], "type": "subject"},
    {"id": "dog", "labels": ["dog", "狗"], "type": "subject"},
    {"id": "person", "labels": ["person", "human", "man", "woman", "人", "男人", "女人"], "type": "subject"},
    {"id": "drone", "labels": ["drone", "quadcopter", "无人机"], "type": "object"},
    {"id": "robot", "labels": ["robot", "机器人"], "type": "subject"},
]


ACTION_PATTERNS = [
    {
        "id": "chase",
        "labels": ["chase", "chases", "chasing", "pursue", "pursues", "追逐", "追赶"],
        "contract": "{actor} follows behind {target}; {target} leads the motion path and escapes forward",
        "spatial": "{target} is ahead of {actor} along the travel direction",
        "negative": "{target} behind {actor}; {actor} ahead of {target}; hovering/static {target}",
    },
    {
        "id": "rush_toward",
        "labels": ["rush toward", "charge toward", "冲向"],
        "contract": "{actor} moves quickly toward {target}; direction of travel points from {actor} to {target}",
        "spatial": "{target} is the destination in front of {actor}",
        "negative": "{actor} moving away from {target}; static pose without forward motion",
    },
    {
        "id": "attack_toward",
        "labels": ["attack toward", "kill toward", "杀向", "攻向"],
        "contract": "{actor} advances aggressively toward {target}; attack intent is readable",
        "spatial": "{target} is in front of {actor} as the attack destination",
        "negative": "{actor} fleeing from {target}; no aggressive motion; target behind actor",
    },
    {
        "id": "pin_down",
        "labels": ["pin down", "press down", "hold down", "压住", "按住"],
        "contract": "{actor} physically restrains {target}; contact and pressure are visible",
        "spatial": "{actor} is above or on top of {target}; {target} is underneath or immobilized",
        "negative": "no physical contact; subjects separated; reversed pressure relationship",
    },
]


SETTING_PATTERNS = [
    ("Shanghai", ["shanghai", "上海"]),
    ("rooftop", ["rooftop", "roof top", "屋顶", "天台", "楼顶"]),
    ("rainy night", ["rainy night", "雨夜"]),
    ("night", ["night", "夜晚", "夜"]),
    ("rain", ["rain", "rainy", "雨"]),
]


def build_semantic_contract(text: str, language: str = "zh") -> dict[str, Any]:
    entities = _extract_entities(text)
    actions = _extract_actions(text, entities)
    settings = _extract_settings(text)
    required_elements = _dedupe(
        [entity["label"] for entity in entities]
        + [setting["label"] for setting in settings if setting["label"] not in {"rain", "night"}]
    )
    identity_constraints = [
        constraint
        for entity in entities
        for constraint in entity.get("identity_constraints", [])
    ]
    spatial_relationships = [
        relationship
        for action in actions
        for relationship in action.get("spatial_relationships", [])
    ]
    motion_contracts = [
        contract
        for action in actions
        for contract in action.get("motion_contracts", [])
    ]
    negative_constraints = [
        constraint
        for entity in entities
        for constraint in entity.get("negative_constraints", [])
    ] + [
        constraint
        for action in actions
        for constraint in action.get("negative_constraints", [])
    ]
    success_criteria = [
        f"{entity['label']} appears as one indivisible visible target"
        for entity in entities
    ] + [
        f"{action['label']} action contract is readable: {'; '.join(action.get('motion_contracts', []))}"
        for action in actions
    ]
    prompt_contract_parts = [
        "ENTITY CONTRACTS: " + "; ".join(identity_constraints) if identity_constraints else "",
        "ACTION CONTRACTS: " + "; ".join(motion_contracts) if motion_contracts else "",
        "SPATIAL CONTRACTS: " + "; ".join(spatial_relationships) if spatial_relationships else "",
    ]
    return {
        "source_text": text,
        "entities": entities,
        "actions": actions,
        "settings": settings,
        "targets": [*entities, *actions, *settings],
        "required_elements": required_elements,
        "identity_constraints": identity_constraints,
        "spatial_relationships": spatial_relationships,
        "motion_contracts": motion_contracts,
        "negative_constraints": _dedupe(negative_constraints),
        "success_criteria": _dedupe(success_criteria),
        "prompt_contract": " ".join(part for part in prompt_contract_parts if part),
    }


def _extract_entities(text: str) -> list[dict[str, Any]]:
    lowered = text.lower()
    entities: list[dict[str, Any]] = []
    for head in ENTITY_HEADS:
        head_label = _first_present(text, lowered, head["labels"])
        if not head_label:
            continue
        modifiers = [
            modifier
            for modifier in ENTITY_MODIFIERS
            if modifier["id"] != head["id"]
            and not (head["id"] == "person" and modifier["id"] == "robot")
            and _modifier_attaches(text, lowered, modifier["labels"], head_label)
        ]
        label = _entity_label(modifiers, head["id"])
        identity_constraints = [
            f"{label} is one indivisible target; do not split its modifier from its base subject",
            *[
                f"{label} must show {trait}"
                for modifier in modifiers
                for trait in modifier["traits"]
            ],
        ] if modifiers else []
        negative_constraints = [
            f"no {modifier['negative']} for {label}"
            for modifier in modifiers
        ]
        entities.append(
            {
                "target_id": f"{head['type']}_{_slug(label)}",
                "type": head["type"],
                "label": label,
                "base_label": head["id"],
                "modifiers": [modifier["id"] for modifier in modifiers],
                "aliases": _entity_aliases(label, head, modifiers),
                "identity_constraints": identity_constraints,
                "negative_constraints": negative_constraints,
                "required": True,
                "visibility": "must_be_visible",
            }
        )
    return _remove_consumed_modifier_entities(_dedupe_targets(entities), lowered)


def _extract_actions(text: str, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lowered = text.lower()
    actions = []
    for pattern in ACTION_PATTERNS:
        if not any(label in lowered or label in text for label in pattern["labels"]):
            continue
        actor, target = _infer_action_roles(text, entities)
        actor_label = actor.get("label", "primary subject") if actor else "primary subject"
        target_label = target.get("label", "target object") if target else "target object"
        actions.append(
            {
                "target_id": f"action_{pattern['id']}",
                "type": "action",
                "label": pattern["id"],
                "actor": actor_label,
                "target": target_label,
                "aliases": pattern["labels"],
                "motion_contracts": [pattern["contract"].format(actor=actor_label, target=target_label)],
                "spatial_relationships": [pattern["spatial"].format(actor=actor_label, target=target_label)],
                "negative_constraints": [pattern["negative"].format(actor=actor_label, target=target_label)],
                "required": True,
                "visibility": "must_be_readable",
            }
        )
    return actions


def _extract_settings(text: str) -> list[dict[str, Any]]:
    lowered = text.lower()
    settings = []
    for label, aliases in SETTING_PATTERNS:
        if any(alias in lowered or alias in text for alias in aliases):
            if label in {"night", "rain"} and any(item["label"] == "rainy night" for item in settings):
                continue
            settings.append(
                {
                    "target_id": f"setting_{_slug(label)}",
                    "type": "setting",
                    "label": label,
                    "aliases": aliases,
                    "required": True,
                    "visibility": "must_be_visible",
                }
            )
    return settings


def _infer_action_roles(text: str, entities: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not entities:
        return None, None
    positions = []
    lowered = text.lower()
    for entity in entities:
        indexes = [
            _find_index(text, lowered, alias)
            for alias in entity.get("aliases", []) + [entity["label"], entity.get("base_label", "")]
        ]
        indexes = [index for index in indexes if index >= 0]
        if indexes:
            positions.append((min(indexes), entity))
    positions.sort(key=lambda item: item[0])
    actor = positions[0][1] if positions else entities[0]
    target = next((entity for _, entity in positions[1:] if entity is not actor), None)
    if target is None:
        target = next((entity for entity in entities if entity is not actor), None)
    return actor, target


def _modifier_attaches(text: str, lowered: str, modifier_labels: list[str], head_label: str) -> bool:
    head_lower = head_label.lower()
    for modifier in modifier_labels:
        modifier_lower = modifier.lower()
        if f"{modifier_lower} {head_lower}" in lowered or f"{modifier}{head_label}" in text:
            return True
        if modifier_lower in lowered:
            modifier_index = lowered.find(modifier_lower)
            head_index = lowered.find(head_lower)
            if head_index >= 0 and 0 <= head_index - modifier_index <= 12:
                return True
    return False


def _entity_label(modifiers: list[dict[str, Any]], head_id: str) -> str:
    if not modifiers:
        return head_id
    return " ".join([*(modifier["id"] for modifier in modifiers), head_id])


def _entity_aliases(label: str, head: dict[str, Any], modifiers: list[dict[str, Any]]) -> list[str]:
    aliases = [label, *head["labels"]]
    for modifier in modifiers:
        aliases.extend(f"{modifier_label} {head_label}" for modifier_label in modifier["labels"] for head_label in head["labels"])
        aliases.extend(f"{modifier_label}{head_label}" for modifier_label in modifier["labels"] for head_label in head["labels"])
    return _dedupe([alias for alias in aliases if alias])


def _first_present(text: str, lowered: str, labels: list[str]) -> str:
    for label in labels:
        if label.lower() in lowered or label in text:
            return label
    return ""


def _find_index(text: str, lowered: str, value: str) -> int:
    if not value:
        return -1
    index = lowered.find(value.lower())
    if index >= 0:
        return index
    return text.find(value)


def _dedupe_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for target in targets:
        key = (target["type"], target["label"])
        if key in seen:
            continue
        seen.add(key)
        result.append(target)
    return result


def _remove_consumed_modifier_entities(targets: list[dict[str, Any]], lowered: str) -> list[dict[str, Any]]:
    consumed_modifiers = {
        modifier
        for target in targets
        for modifier in target.get("modifiers", [])
    }
    result = []
    for target in targets:
        label = str(target.get("label", ""))
        if (
            not target.get("modifiers")
            and label in consumed_modifiers
            and lowered.count(label.lower()) <= 1
        ):
            continue
        result.append(target)
    return result


def _dedupe(values: list[str]) -> list[str]:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return seen


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
