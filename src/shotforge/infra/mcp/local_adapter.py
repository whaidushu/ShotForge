from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shotforge.config import get_settings
from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.project_state import ProjectState
from shotforge.core.runtime_models import MCPAccessRecord
from shotforge.core.knowledge_base import KnowledgeBase
from shotforge.infra.mcp.schema import (
    MCPAccessPolicy,
    MCPPromptSpec,
    MCPResourceSpec,
    MCPServerInfo,
    MCPToolResult,
    MCPToolSpec,
)


class LocalMCPAdapter:
    """MCP-like local adapter exposing ShotForge capabilities as tools/resources."""

    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        access_policy: MCPAccessPolicy | None = None,
    ):
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.access_policy = access_policy or MCPAccessPolicy()
        self._access_records: list[MCPAccessRecord] = []
        self._tools = {
            "knowledge.search": MCPToolSpec(
                name="knowledge.search",
                description="Search local ShotForge knowledge assets.",
                input_schema={"query": "string", "tags": "list[string]", "limit": "integer"},
                output_schema={"items": "list[object]"},
            ),
            "runs.list": MCPToolSpec(
                name="runs.list",
                description="List local ShotForge run ids.",
                input_schema={"limit": "integer"},
                output_schema={"run_ids": "list[string]"},
            ),
            "runs.get_package": MCPToolSpec(
                name="runs.get_package",
                description="Read a generated package.json by run id.",
                input_schema={"run_id": "string"},
                output_schema={"package": "object"},
            ),
            "runs.get_harness_audit": MCPToolSpec(
                name="runs.get_harness_audit",
                description="Read runtime evidence data for a run id.",
                input_schema={"run_id": "string"},
                output_schema={"harness_audit": "object"},
            ),
        }
        if not self.access_policy.allowed_tools:
            self.access_policy.allowed_tools = sorted(self._tools)
        self._prompts = {
            "shotforge.run_review": MCPPromptSpec(
                name="shotforge.run_review",
                description="Summarize a ShotForge run for review/refine.",
                arguments={"run_id": "string"},
                template=(
                    "Review ShotForge run {run_id}. Focus on runtime evidence, "
                    "provider readiness, evaluation issues, and next actions."
                ),
                metadata={"kind": "review_refine"},
            )
        }

    def server_info(self) -> MCPServerInfo:
        return MCPServerInfo(
            capabilities=[
                "tools/list",
                "tools/call",
                "resources/list",
                "resources/read",
                "prompts/list",
                "shotforge/run-audit",
            ]
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "server": self.server_info().model_dump(mode="json"),
            "tools": [tool.model_dump(mode="json") for tool in self.list_tools()],
            "resources": [resource.model_dump(mode="json") for resource in self.list_resources()],
            "prompts": [prompt.model_dump(mode="json") for prompt in self.list_prompts()],
            "access_policy": self.access_policy.model_dump(mode="json"),
        }

    def list_tools(self) -> list[MCPToolSpec]:
        self._record_access("tools/list", "", "completed", "allowed", "policy_allowed")
        return [
            tool
            for name, tool in self._tools.items()
            if name in set(self.access_policy.allowed_tools)
        ]

    def list_prompts(self) -> list[MCPPromptSpec]:
        decision = "allowed" if self.access_policy.expose_prompts else "denied"
        status = "completed" if decision == "allowed" else "denied"
        self._record_access("prompts/list", "", status, decision, "prompt_policy")
        if not self.access_policy.expose_prompts:
            return []
        return list(self._prompts.values())

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> MCPToolResult:
        arguments = arguments or {}
        allowed, reason = self._tool_allowed(name)
        if not allowed:
            self._record_access("tools/call", name, "denied", "denied", reason)
            return MCPToolResult(
                tool_name=name,
                status="failed",
                is_error=True,
                error=reason,
                metadata={"access_policy": self.access_policy.model_dump(mode="json")},
            )
        if name not in self._tools:
            self._record_access("tools/call", name, "failed", "allowed", "tool_not_found")
            return MCPToolResult(
                tool_name=name,
                status="failed",
                is_error=True,
                error=f"MCP tool not found: {name}",
            )
        if name == "knowledge.search":
            items = [
                item.model_dump(mode="json")
                for item in self.knowledge_base.search(
                    query=str(arguments.get("query", "")),
                    tags=list(arguments.get("tags", [])),
                    limit=int(arguments.get("limit", 5)),
                )
            ]
            self._record_access("tools/call", name, "completed", "allowed", "policy_allowed")
            return MCPToolResult(tool_name=name, result={"items": items})
        if name == "runs.list":
            self._record_access("tools/call", name, "completed", "allowed", "policy_allowed")
            return MCPToolResult(tool_name=name, result={"run_ids": self._list_runs(arguments)})
        try:
            if name == "runs.get_package":
                self._record_access("tools/call", name, "completed", "allowed", "policy_allowed")
                return MCPToolResult(tool_name=name, result={"package": self._get_package(arguments)})
            if name == "runs.get_harness_audit":
                package = self._get_package(arguments)
                state = ProjectState.model_validate(package)
                self._record_access("tools/call", name, "completed", "allowed", "policy_allowed")
                return MCPToolResult(
                    tool_name=name,
                    result={"harness_audit": build_harness_audit(state)},
                )
        except Exception as exc:
            self._record_access("tools/call", name, "failed", "allowed", str(exc))
            return MCPToolResult(
                tool_name=name,
                status="failed",
                is_error=True,
                error=str(exc),
            )
        return MCPToolResult(tool_name=name, result={})

    def list_resources(self) -> list[MCPResourceSpec]:
        self._record_access("resources/list", "", "completed", "allowed", "policy_allowed")
        resources: list[MCPResourceSpec] = []
        for run_id in self._run_dirs():
            resources.extend(
                [
                    MCPResourceSpec(
                        uri=f"shotforge://runs/{run_id}/package",
                        name=f"{run_id} package",
                        description="ShotForge ProjectState package JSON",
                        metadata={"run_id": run_id, "kind": "package"},
                    ),
                    MCPResourceSpec(
                        uri=f"shotforge://runs/{run_id}/harness",
                        name=f"{run_id} runtime evidence",
                        description="ShotForge runtime evidence JSON",
                        metadata={"run_id": run_id, "kind": "harness_audit"},
                    ),
                ]
            )
        return resources

    def read_resource(self, uri: str) -> dict[str, Any]:
        allowed, reason = self._resource_allowed(uri)
        if not allowed:
            self._record_access("resources/read", uri, "denied", "denied", reason)
            raise PermissionError(reason)
        prefix = "shotforge://runs/"
        if not uri.startswith(prefix):
            self._record_access("resources/read", uri, "failed", "allowed", "unsupported_uri")
            raise ValueError(f"Unsupported resource uri: {uri}")
        if uri.endswith("/package"):
            run_id = uri[len(prefix) : -len("/package")]
            self._record_access("resources/read", uri, "completed", "allowed", "policy_allowed")
            return self._read_package(run_id)
        if uri.endswith("/harness"):
            run_id = uri[len(prefix) : -len("/harness")]
            self._record_access("resources/read", uri, "completed", "allowed", "policy_allowed")
            return build_harness_audit(ProjectState.model_validate(self._read_package(run_id)))
        self._record_access("resources/read", uri, "failed", "allowed", "unsupported_uri")
        raise ValueError(f"Unsupported resource uri: {uri}")

    def access_records(self) -> list[MCPAccessRecord]:
        return list(self._access_records)

    def _list_runs(self, arguments: dict[str, Any]) -> list[str]:
        limit = min(int(arguments.get("limit", 20)), self.access_policy.max_runs_list_limit)
        return self._run_dirs()[:limit]

    def _run_dirs(self) -> list[str]:
        runs_dir = get_settings().runs_dir
        if not runs_dir.exists():
            return []
        return [
            path.name
            for path in sorted(runs_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
            if path.is_dir()
        ]

    def _get_package(self, arguments: dict[str, Any]) -> dict[str, Any]:
        run_id = str(arguments.get("run_id", ""))
        return self._read_package(run_id)

    def _read_package(self, run_id: str) -> dict[str, Any]:
        package_path = Path(get_settings().runs_dir) / run_id / "package.json"
        if not package_path.exists():
            raise FileNotFoundError(f"Run package not found: {run_id}")
        return json.loads(package_path.read_text(encoding="utf-8"))

    def _tool_allowed(self, name: str) -> tuple[bool, str]:
        if self.access_policy.require_known_tool and name not in self._tools:
            return False, f"MCP tool not found: {name}"
        if name not in set(self.access_policy.allowed_tools):
            return False, f"MCP tool denied by policy: {name}"
        return True, "policy_allowed"

    def _resource_allowed(self, uri: str) -> tuple[bool, str]:
        for prefix in self.access_policy.allowed_resource_prefixes:
            if uri.startswith(prefix):
                return True, "policy_allowed"
        return False, f"MCP resource denied by policy: {uri}"

    def _record_access(
        self,
        operation: str,
        target: str,
        status: str,
        decision: str,
        reason: str,
    ) -> None:
        self._access_records.append(
            MCPAccessRecord(
                operation=operation,  # type: ignore[arg-type]
                target=target,
                status=status,  # type: ignore[arg-type]
                decision=decision,  # type: ignore[arg-type]
                reason=reason,
                metadata={"policy": self.access_policy.model_dump(mode="json")},
            )
        )


def build_default_mcp_adapter() -> LocalMCPAdapter:
    return LocalMCPAdapter()
