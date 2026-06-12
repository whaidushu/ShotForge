from __future__ import annotations

from typing import Any


class RepairStrategyCatalog:
    """Rule-based first pass for turning target failures into repair actions.

    The catalog is intentionally small and declarative. Future work can replace or
    extend entries with provider-specific adapters, learned prompt patches, or
    workflow-control recommendations without changing the target matrix contract.
    """

    def prompt_patch(self, row: dict[str, Any]) -> dict[str, Any]:
        target = str(row.get("target") or row.get("label") or "target")
        target_type = str(row.get("target_type", "object"))
        failure_reason = str(row.get("failure_reason", "unresolved"))
        repair_type = "control_needed" if failure_reason == "control_needed" else "prompt_patch"
        return {
            "target": target,
            "target_id": row.get("target_id", ""),
            "repair_type": repair_type,
            "failure_reason": failure_reason,
            "change": row.get("repair_suggestion") or self._default_change(target, target_type),
        }

    def negative_patch(self, row: dict[str, Any]) -> str:
        target = str(row.get("target") or row.get("label") or "").strip()
        if str(row.get("target_type")) == "negative_constraint" and target:
            return target
        suggestion = str(row.get("repair_suggestion", "")).strip()
        return suggestion if "avoid" in suggestion.lower() else ""

    def preservation_lock(self, row: dict[str, Any]) -> dict[str, Any]:
        target = str(row.get("target") or row.get("label") or "target")
        return {
            "target": target,
            "target_id": row.get("target_id", ""),
            "score": row.get("score", 0.0),
            "frame_presence": f"{len(row.get('frame_hits', []) or [])}/{row.get('sampled_frame_count', 0)}",
            "lock": row.get("lock_suggestion")
            or f"preserve {target} with at least the same visibility as the source iteration",
        }

    def _default_change(self, target: str, target_type: str) -> str:
        if target_type == "setting":
            return (
                f"make {target} visible with concrete scene anchors, recognizable geometry, "
                "and background details"
            )
        if target_type == "action":
            return f"make {target} readable through actor, target, direction, and visible motion result"
        if target_type == "spatial_relation":
            return f"make {target} explicit through screen position and separated silhouettes"
        return f"make {target} clearly visible, separable, and measurable in the frame"
