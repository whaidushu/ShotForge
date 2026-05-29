from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, Field

from shotforge.core.runtime_models import ToolCallRecord


Skill = Callable[..., Any]
ToolRiskLevel = Literal["low", "medium", "high"]


class ToolExecutionPolicy(BaseModel):
    allowed_permission_scopes: set[str] = Field(
        default_factory=lambda: {"local", "local_inference", "local_file_write"}
    )
    max_total_calls: int = 100
    max_calls_per_tool: int = 20
    require_approval_for_high_risk: bool = True


class SkillSpec(BaseModel):
    name: str
    description: str = ""
    permission_scope: str = "local"
    risk_level: ToolRiskLevel = "low"
    requires_approval: bool = False
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillRegistry:
    def __init__(self, policy: ToolExecutionPolicy | None = None):
        self._skills: dict[str, Skill] = {}
        self._specs: dict[str, SkillSpec] = {}
        self._records: list[ToolCallRecord] = []
        self.policy = policy or ToolExecutionPolicy()
        self._call_counts: dict[str, int] = {}

    def register(
        self,
        name: str,
        skill: Skill,
        *,
        description: str = "",
        permission_scope: str = "local",
        risk_level: ToolRiskLevel = "low",
        requires_approval: bool = False,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if name in self._skills:
            raise ValueError(f"Skill already registered: {name}")
        self._skills[name] = skill
        self._specs[name] = SkillSpec(
            name=name,
            description=description,
            permission_scope=permission_scope,
            risk_level=risk_level,
            requires_approval=requires_approval,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            metadata=metadata or {},
        )

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise KeyError(f"Skill not registered: {name}") from exc

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        spec = self.spec(name)
        started = perf_counter()
        input_preview = self._preview({"args": args, "kwargs": kwargs})
        purpose = str(kwargs.get("purpose", ""))
        try:
            self._authorize(spec)
        except PermissionError as exc:
            self._records.append(
                ToolCallRecord(
                    tool_name=name,
                    status="failed",
                    duration_ms=(perf_counter() - started) * 1000,
                    input_preview=input_preview,
                    error=str(exc),
                    permission_scope=spec.permission_scope,
                    metadata=self._record_metadata(spec, purpose, authorized=False),
                )
            )
            raise
        try:
            result = self.get(name)(*args, **kwargs)
        except Exception as exc:
            self._records.append(
                ToolCallRecord(
                    tool_name=name,
                    status="failed",
                    duration_ms=(perf_counter() - started) * 1000,
                    input_preview=input_preview,
                    error=str(exc),
                    permission_scope=spec.permission_scope,
                    metadata=self._record_metadata(spec, purpose, authorized=True),
                )
            )
            raise
        self._call_counts[name] = self._call_counts.get(name, 0) + 1
        self._records.append(
            ToolCallRecord(
                tool_name=name,
                status="completed",
                duration_ms=(perf_counter() - started) * 1000,
                input_preview=input_preview,
                output_preview=self._preview(result),
                permission_scope=spec.permission_scope,
                metadata=self._record_metadata(spec, purpose, authorized=True),
            )
        )
        return result

    def names(self) -> list[str]:
        return sorted(self._skills)

    def spec(self, name: str) -> SkillSpec:
        if name not in self._specs:
            raise KeyError(f"Skill not registered: {name}")
        return self._specs[name]

    def records(self) -> list[ToolCallRecord]:
        return list(self._records)

    def call_counts(self) -> dict[str, int]:
        return dict(self._call_counts)

    def _authorize(self, spec: SkillSpec) -> None:
        total_calls = sum(self._call_counts.values())
        tool_calls = self._call_counts.get(spec.name, 0)
        if spec.permission_scope not in self.policy.allowed_permission_scopes:
            raise PermissionError(
                f"Tool permission scope denied: {spec.name} ({spec.permission_scope})"
            )
        if total_calls >= self.policy.max_total_calls:
            raise PermissionError(f"Tool total call budget exceeded: {self.policy.max_total_calls}")
        if tool_calls >= self.policy.max_calls_per_tool:
            raise PermissionError(
                f"Tool call budget exceeded for {spec.name}: {self.policy.max_calls_per_tool}"
            )
        if (
            self.policy.require_approval_for_high_risk
            and spec.risk_level == "high"
            and not spec.requires_approval
        ):
            raise PermissionError(f"High-risk tool requires explicit approval flag: {spec.name}")

    def _record_metadata(
        self,
        spec: SkillSpec,
        purpose: str,
        *,
        authorized: bool,
    ) -> dict[str, Any]:
        return {
            "purpose": purpose,
            "authorized": authorized,
            "risk_level": spec.risk_level,
            "requires_approval": spec.requires_approval,
            "description": spec.description,
            "call_count_before": self._call_counts.get(spec.name, 0),
            "policy": self.policy.model_dump(mode="json"),
        }

    def _preview(self, value: Any, limit: int = 240) -> str:
        text = repr(value)
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."


__all__ = ["SkillRegistry", "SkillSpec", "ToolExecutionPolicy"]
