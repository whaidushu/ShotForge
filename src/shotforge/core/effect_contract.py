from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field


EffectLayer = Literal[
    "physical",
    "consistency",
    "style",
    "atmosphere",
    "creative_control",
]
EffectTargetType = Literal[
    "subject",
    "object",
    "setting",
    "attribute",
    "count",
    "action",
    "spatial_relation",
    "negative_constraint",
    "creative_control",
]


class CreativeControl(BaseModel):
    """Reserved interface for user-facing creative controls.

    These controls intentionally stay separate from hard physical targets so future
    UI sliders such as cinematic intensity, commercial polish, reversal strength,
    or animation exaggeration can map to provider-specific prompt/control patches.
    """

    control_id: str
    label: str
    layer: EffectLayer = "creative_control"
    value: float | str | bool | None = None
    intent: str = ""
    provider_hints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EffectTarget(BaseModel):
    target_id: str
    label: str
    layer: EffectLayer = "physical"
    target_type: EffectTargetType
    shot_id: str = "shot_001"
    aliases: list[str] = Field(default_factory=list)
    required: bool = True
    weight: float = 1.0
    threshold: float = 0.75
    evidence_rule: str = ""
    repair_strategy: str = "prompt_patch"
    lock_policy: str = "lock_when_passed"
    prompt_hints: list[str] = Field(default_factory=list)
    negative_hints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EffectContract(BaseModel):
    contract_id: str
    version: str = "0.1"
    source_text: str = ""
    language: str = "en"
    shot_id: str = "shot_001"
    targets: list[EffectTarget] = Field(default_factory=list)
    creative_controls: list[CreativeControl] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def target_by_label(self) -> dict[str, EffectTarget]:
        result: dict[str, EffectTarget] = {}
        for target in self.targets:
            result[target.label.lower()] = target
            for alias in target.aliases:
                result.setdefault(alias.lower(), target)
        return result


def build_effect_contract(
    payload: dict[str, Any],
    *,
    source_text: str = "",
    language: str = "en",
    shot_id: str = "shot_001",
    contract_id: str | None = None,
    creative_controls: list[dict[str, Any]] | None = None,
) -> EffectContract:
    """Build a normalized effect contract from physical/semantic target payloads.

    The input format is deliberately loose so existing semantic extraction, case
    files, or future model-specific extractors can all feed the same contract.
    """

    targets: list[EffectTarget] = []
    for item in payload.get("targets", []) or []:
        if not isinstance(item, dict):
            continue
        targets.append(_target_from_payload(item, shot_id=shot_id))

    existing_labels = {target.label.lower() for target in targets}
    for label in payload.get("required_elements", []) or []:
        text = str(label).strip()
        if not text or text.lower() in existing_labels:
            continue
        target = EffectTarget(
            target_id=f"element.{_slug(text)}",
            label=text,
            target_type="object",
            shot_id=shot_id,
            aliases=[text],
            evidence_rule="The visible result contains the required element.",
            repair_strategy="prompt_patch",
        )
        targets.append(target)
        existing_labels.add(text.lower())

    targets.extend(
        _relationship_targets(
            payload.get("spatial_relationships", []) or [],
            target_type="spatial_relation",
            shot_id=shot_id,
        )
    )
    targets.extend(
        _relationship_targets(
            payload.get("motion_contracts", []) or [],
            target_type="action",
            shot_id=shot_id,
        )
    )
    targets.extend(
        _negative_constraint_targets(payload.get("negative_constraints", []) or [], shot_id=shot_id)
    )

    deduped_targets = _dedupe_targets(targets)
    controls = [
        CreativeControl.model_validate(item)
        for item in creative_controls or payload.get("creative_controls", []) or []
        if isinstance(item, dict)
    ]
    return EffectContract(
        contract_id=contract_id or f"effect.{_slug(source_text or payload.get('source_text', '') or shot_id)}",
        source_text=source_text or str(payload.get("source_text", "")),
        language=language,
        shot_id=shot_id,
        targets=deduped_targets,
        creative_controls=controls,
        metadata={
            "source": "physical_targets_payload",
            "prompt_contract": payload.get("prompt_contract", ""),
            "identity_constraints": payload.get("identity_constraints", []),
            "success_criteria": payload.get("success_criteria", []),
        },
    )


def _target_from_payload(item: dict[str, Any], *, shot_id: str) -> EffectTarget:
    label = str(item.get("label") or item.get("target") or item.get("target_id") or "").strip()
    target_type = _target_type(str(item.get("type", "object")))
    target_id = str(item.get("target_id") or f"{target_type}.{_slug(label)}")
    return EffectTarget(
        target_id=_normalize_target_id(target_id, target_type, label),
        label=label,
        layer=_layer_for_type(target_type),
        target_type=target_type,
        shot_id=str(item.get("shot_id") or shot_id),
        aliases=[str(alias) for alias in item.get("aliases", []) if str(alias).strip()],
        required=bool(item.get("required", True)),
        weight=float(item.get("weight", 1.0) or 1.0),
        threshold=float(item.get("threshold", _threshold_for_type(target_type)) or 0.75),
        evidence_rule=_evidence_rule(target_type),
        repair_strategy=_repair_strategy(target_type),
        prompt_hints=[str(value) for value in item.get("identity_constraints", [])],
        negative_hints=[str(value) for value in item.get("negative_constraints", [])],
        metadata={
            key: value
            for key, value in item.items()
            if key
            not in {
                "target_id",
                "label",
                "target",
                "type",
                "shot_id",
                "aliases",
                "required",
                "weight",
                "threshold",
            }
        },
    )


def _relationship_targets(
    values: list[Any],
    *,
    target_type: Literal["action", "spatial_relation"],
    shot_id: str,
) -> list[EffectTarget]:
    targets = []
    for index, value in enumerate(values):
        text = str(value).strip()
        if not text:
            continue
        targets.append(
            EffectTarget(
                target_id=f"{target_type}.{index + 1}.{_slug(text)[:48]}",
                label=text,
                layer="physical" if target_type == "spatial_relation" else "consistency",
                target_type=target_type,
                shot_id=shot_id,
                aliases=[text],
                threshold=0.72 if target_type == "spatial_relation" else 0.75,
                evidence_rule=(
                    "The observed frames show the requested relative position."
                    if target_type == "spatial_relation"
                    else "The observed frames show the action contract as readable motion."
                ),
                repair_strategy="prompt_patch",
            )
        )
    return targets


def _negative_constraint_targets(values: list[Any], *, shot_id: str) -> list[EffectTarget]:
    targets = []
    for index, value in enumerate(values):
        text = str(value).strip()
        if not text:
            continue
        targets.append(
            EffectTarget(
                target_id=f"negative.{index + 1}.{_slug(text)[:48]}",
                label=text,
                layer="physical",
                target_type="negative_constraint",
                shot_id=shot_id,
                required=True,
                threshold=0.9,
                evidence_rule="The observed frames avoid the prohibited failure mode.",
                repair_strategy="negative_patch",
                negative_hints=[text],
            )
        )
    return targets


def _target_type(value: str) -> EffectTargetType:
    normalized = value.strip().lower()
    if normalized in {
        "subject",
        "object",
        "setting",
        "attribute",
        "count",
        "action",
        "spatial_relation",
        "negative_constraint",
        "creative_control",
    }:
        return normalized  # type: ignore[return-value]
    if normalized in {"atmosphere", "scene"}:
        return "setting"
    return "object"


def _layer_for_type(target_type: EffectTargetType) -> EffectLayer:
    if target_type in {"action"}:
        return "consistency"
    if target_type == "creative_control":
        return "creative_control"
    return "physical"


def _threshold_for_type(target_type: EffectTargetType) -> float:
    return {
        "subject": 0.78,
        "object": 0.75,
        "setting": 0.72,
        "attribute": 0.78,
        "count": 0.9,
        "action": 0.75,
        "spatial_relation": 0.72,
        "negative_constraint": 0.9,
        "creative_control": 0.65,
    }[target_type]


def _repair_strategy(target_type: EffectTargetType) -> str:
    if target_type == "negative_constraint":
        return "negative_patch"
    if target_type == "creative_control":
        return "creative_control_patch"
    return "prompt_patch"


def _evidence_rule(target_type: EffectTargetType) -> str:
    return {
        "subject": "The required subject is visible as a stable, separable target.",
        "object": "The required object is visible as a separable target.",
        "setting": "The required setting has concrete visual anchors.",
        "attribute": "The required attribute is attached to the correct target.",
        "count": "The observed subject count matches the requested count.",
        "action": "The action is readable across sampled frames.",
        "spatial_relation": "The relative position between targets is visible.",
        "negative_constraint": "The prohibited failure mode is absent.",
        "creative_control": "The creative control is expressed in visible cinematic language.",
    }[target_type]


def _dedupe_targets(targets: list[EffectTarget]) -> list[EffectTarget]:
    result: list[EffectTarget] = []
    seen: set[tuple[str, str, str]] = set()
    for target in targets:
        key = (target.shot_id, target.target_type, target.label.lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(target)
    return result


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "target"


def _normalize_target_id(target_id: str, target_type: EffectTargetType, label: str) -> str:
    if "." in target_id:
        return target_id
    prefix = f"{target_type}_"
    if target_id.startswith(prefix):
        return f"{target_type}.{target_id[len(prefix):]}"
    return f"{target_type}.{_slug(label)}"
