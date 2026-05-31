from __future__ import annotations

import inspect
from collections.abc import Callable
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, Field

from shotforge.core.runtime_models import ToolCallRecord, ToolOrchestrationRecord


Skill = Callable[..., Any]
ToolRiskLevel = Literal["low", "medium", "high"]


class ToolExecutionPolicy(BaseModel):
    allowed_permission_scopes: set[str] = Field(
        default_factory=lambda: {"local", "local_inference", "external_llm", "local_file_write"}
    )
    max_total_calls: int = 100
    max_calls_per_tool: int = 20
    require_approval_for_high_risk: bool = True
    require_purpose_for_high_risk: bool = True
    allow_fallback_tools: bool = True
    validate_tool_schemas: bool = True


class SkillSpec(BaseModel):
    name: str
    description: str = ""
    permission_scope: str = "local"
    risk_level: ToolRiskLevel = "low"
    requires_approval: bool = False
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionRequest(BaseModel):
    tool_name: str
    agent_name: str = ""
    purpose: str = ""
    expected_output: str = ""
    fallback_tools: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolPolicyDecision(BaseModel):
    tool_name: str
    decision: Literal["allowed", "denied"]
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillRegistry:
    def __init__(self, policy: ToolExecutionPolicy | None = None):
        self._skills: dict[str, Skill] = {}
        self._specs: dict[str, SkillSpec] = {}
        self._records: list[ToolCallRecord] = []
        self._orchestration_records: list[ToolOrchestrationRecord] = []
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
        agent_name = str(kwargs.pop("agent_name", ""))
        expected_output = str(kwargs.pop("expected_output", ""))
        fallback_tools = list(kwargs.pop("fallback_tools", []) or [])
        tool_plan_id = str(kwargs.pop("tool_plan_id", ""))
        purpose = str(kwargs.get("purpose", ""))
        request = ToolExecutionRequest(
            tool_name=name,
            agent_name=agent_name,
            purpose=purpose,
            expected_output=expected_output,
            fallback_tools=fallback_tools,
            metadata={"input_preview": self._preview({"args": args, "kwargs": kwargs})},
        )
        orchestration = ToolOrchestrationRecord(
            requested_tool=name,
            selected_tool=name,
            agent_name=agent_name,
            purpose=purpose,
            expected_output=expected_output,
            fallback_tools=fallback_tools,
            metadata={
                "request": request.model_dump(mode="json"),
                "policy": self.policy.model_dump(mode="json"),
            },
        )
        if tool_plan_id:
            orchestration.plan_id = tool_plan_id

        try:
            result = self._execute_once(name, args, kwargs, orchestration)
        except Exception as primary_exc:
            if not self.policy.allow_fallback_tools or not fallback_tools:
                orchestration.status = (
                    "denied" if orchestration.authorization_decision == "denied" else "failed"
                )
                self._orchestration_records.append(orchestration)
                raise
            last_exc: Exception = primary_exc
            for fallback_tool in fallback_tools:
                try:
                    result = self._execute_once(fallback_tool, args, kwargs, orchestration)
                except Exception as exc:
                    last_exc = exc
                    continue
                orchestration.selected_tool = fallback_tool
                orchestration.fallback_used = True
                orchestration.status = "fallback_completed"
                self._orchestration_records.append(orchestration)
                return result
            orchestration.fallback_used = True
            orchestration.status = "fallback_failed"
            self._orchestration_records.append(orchestration)
            raise last_exc

        orchestration.status = "completed"
        self._orchestration_records.append(orchestration)
        return result

    def names(self) -> list[str]:
        return sorted(self._skills)

    def spec(self, name: str) -> SkillSpec:
        if name not in self._specs:
            raise KeyError(f"Skill not registered: {name}")
        return self._specs[name]

    def records(self) -> list[ToolCallRecord]:
        return list(self._records)

    def orchestration_records(self) -> list[ToolOrchestrationRecord]:
        return list(self._orchestration_records)

    def call_counts(self) -> dict[str, int]:
        return dict(self._call_counts)

    def _execute_once(
        self,
        name: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        orchestration: ToolOrchestrationRecord,
    ) -> Any:
        spec = self.spec(name)
        started = perf_counter()
        input_preview = self._preview({"args": args, "kwargs": kwargs})
        purpose = str(kwargs.get("purpose", ""))
        orchestration.attempted_tools.append(name)

        decision = self._authorize_decision(spec, purpose)
        orchestration.authorization_decision = decision.decision
        orchestration.authorization_reasons.extend(decision.reasons)
        if decision.decision == "denied":
            error = "; ".join(decision.reasons)
            self._records.append(
                ToolCallRecord(
                    tool_name=name,
                    status="failed",
                    duration_ms=(perf_counter() - started) * 1000,
                    input_preview=input_preview,
                    error=error,
                    permission_scope=spec.permission_scope,
                    metadata=self._record_metadata(
                        spec,
                        purpose,
                        authorized=False,
                        orchestration=orchestration,
                    ),
                )
            )
            raise PermissionError(error)

        try:
            self._validate_input_schema(spec, args, kwargs)
            result = self.get(name)(*args, **self._tool_kwargs(name, kwargs))
            self._validate_output_schema(spec, result)
        except Exception as exc:
            if isinstance(exc, ValueError):
                orchestration.schema_status = "failed"
                orchestration.schema_issues.append(str(exc))
            self._records.append(
                ToolCallRecord(
                    tool_name=name,
                    status="failed",
                    duration_ms=(perf_counter() - started) * 1000,
                    input_preview=input_preview,
                    error=str(exc),
                    permission_scope=spec.permission_scope,
                    metadata=self._record_metadata(
                        spec,
                        purpose,
                        authorized=True,
                        orchestration=orchestration,
                    ),
                )
            )
            raise

        self._call_counts[name] = self._call_counts.get(name, 0) + 1
        if orchestration.schema_status != "failed":
            orchestration.schema_status = "passed" if spec.input_schema or spec.output_schema else "skipped"
        self._records.append(
            ToolCallRecord(
                tool_name=name,
                status="completed",
                duration_ms=(perf_counter() - started) * 1000,
                input_preview=input_preview,
                output_preview=self._preview(result),
                permission_scope=spec.permission_scope,
                metadata=self._record_metadata(
                    spec,
                    purpose,
                    authorized=True,
                    orchestration=orchestration,
                ),
            )
        )
        return result

    def _authorize_decision(self, spec: SkillSpec, purpose: str) -> ToolPolicyDecision:
        total_calls = sum(self._call_counts.values())
        tool_calls = self._call_counts.get(spec.name, 0)
        reasons: list[str] = []
        if spec.permission_scope not in self.policy.allowed_permission_scopes:
            reasons.append(f"permission_scope_denied:{spec.permission_scope}")
        if total_calls >= self.policy.max_total_calls:
            reasons.append(f"total_call_budget_exceeded:{self.policy.max_total_calls}")
        if tool_calls >= self.policy.max_calls_per_tool:
            reasons.append(f"tool_call_budget_exceeded:{self.policy.max_calls_per_tool}")
        if (
            self.policy.require_approval_for_high_risk
            and spec.risk_level == "high"
            and not spec.requires_approval
        ):
            reasons.append("high_risk_requires_approval")
        if self.policy.require_purpose_for_high_risk and spec.risk_level == "high" and not purpose:
            reasons.append("high_risk_requires_purpose")
        return ToolPolicyDecision(
            tool_name=spec.name,
            decision="denied" if reasons else "allowed",
            reasons=reasons or ["policy_allowed"],
            metadata={
                "total_calls_before": total_calls,
                "tool_calls_before": tool_calls,
                "policy": self.policy.model_dump(mode="json"),
            },
        )

    def _validate_input_schema(
        self,
        spec: SkillSpec,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        if not self.policy.validate_tool_schemas or not spec.input_schema:
            return
        required_arg_count = int(spec.input_schema.get("required_arg_count", 0))
        if len(args) < required_arg_count:
            raise ValueError(
                f"Input schema failed for {spec.name}: required_arg_count={required_arg_count}"
            )
        missing_kwargs = [
            key for key in spec.input_schema.get("required_kwargs", []) if key not in kwargs
        ]
        if missing_kwargs:
            raise ValueError(f"Input schema failed for {spec.name}: missing_kwargs={missing_kwargs}")

    def _validate_output_schema(self, spec: SkillSpec, result: Any) -> None:
        if not self.policy.validate_tool_schemas or not spec.output_schema:
            return
        expected_type = spec.output_schema.get("type")
        type_map = {
            "str": str,
            "dict": dict,
            "list": list,
            "int": int,
            "float": float,
            "bool": bool,
        }
        if expected_type in type_map and not isinstance(result, type_map[expected_type]):
            raise ValueError(
                f"Output schema failed for {spec.name}: expected {expected_type}, "
                f"got {type(result).__name__}"
            )

    def _tool_kwargs(self, name: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        skill = self.get(name)
        signature = inspect.signature(skill)
        if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
            return dict(kwargs)
        accepted = {
            key
            for key, param in signature.parameters.items()
            if param.kind
            in {inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
        }
        return {key: value for key, value in kwargs.items() if key in accepted}

    def _record_metadata(
        self,
        spec: SkillSpec,
        purpose: str,
        *,
        authorized: bool,
        orchestration: ToolOrchestrationRecord | None = None,
    ) -> dict[str, Any]:
        return {
            "purpose": purpose,
            "authorized": authorized,
            "risk_level": spec.risk_level,
            "requires_approval": spec.requires_approval,
            "description": spec.description,
            "call_count_before": self._call_counts.get(spec.name, 0),
            "policy": self.policy.model_dump(mode="json"),
            "orchestration": orchestration.model_dump(mode="json") if orchestration else {},
        }

    def _preview(self, value: Any, limit: int = 240) -> str:
        text = repr(value)
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."


__all__ = [
    "SkillRegistry",
    "SkillSpec",
    "ToolExecutionPolicy",
    "ToolExecutionRequest",
    "ToolPolicyDecision",
]
