from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any

from pydantic import BaseModel, Field

from shotforge.core.execution_policy import RiskLevel
from shotforge.core.tool_call import ToolCallRecord


Skill = Callable[..., Any]


class SkillSpec(BaseModel):
    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    permission_scope: str = "local"
    risk_level: RiskLevel = "low"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._specs: dict[str, SkillSpec] = {}
        self._records: list[ToolCallRecord] = []

    def register(
        self,
        name: str,
        skill: Skill,
        spec: SkillSpec | None = None,
    ) -> None:
        if name in self._skills:
            raise ValueError(f"Skill already registered: {name}")
        self._skills[name] = skill
        self._specs[name] = spec or SkillSpec(name=name, description=f"Skill callable: {name}")

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise KeyError(f"Skill not registered: {name}") from exc

    def spec(self, name: str) -> SkillSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise KeyError(f"Skill spec not registered: {name}") from exc

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        started = perf_counter()
        record = ToolCallRecord(
            tool_name=name,
            status="started",
            input_preview=self._preview(args, kwargs),
            metadata={"permission_scope": self.spec(name).permission_scope},
        )
        self._records.append(record)
        try:
            output = self.get(name)(*args, **kwargs)
        except Exception as exc:
            record.status = "failed"
            record.latency_ms = (perf_counter() - started) * 1000
            record.error = str(exc)
            raise
        record.status = "completed"
        record.latency_ms = (perf_counter() - started) * 1000
        record.output_preview = self._preview_output(output)
        return output

    def names(self) -> list[str]:
        return sorted(self._skills)

    def specs(self) -> list[SkillSpec]:
        return [self._specs[name] for name in self.names()]

    def records(self) -> list[ToolCallRecord]:
        return list(self._records)

    def drain_records(self) -> list[ToolCallRecord]:
        records = list(self._records)
        self._records.clear()
        return records

    def _preview(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        return {
            "args_count": len(args),
            "kwargs_keys": sorted(kwargs),
            "first_arg_type": type(args[0]).__name__ if args else "",
        }

    def _preview_output(self, output: Any) -> dict[str, Any]:
        return {
            "type": type(output).__name__,
            "repr": repr(output)[:300],
        }


__all__ = ["Skill", "SkillRegistry", "SkillSpec"]
