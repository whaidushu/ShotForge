from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shotforge.config import get_settings
from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.project_state import ProjectState
from shotforge.core.knowledge_base import KnowledgeBase
from shotforge.infra.mcp.schema import MCPResourceSpec, MCPServerInfo, MCPToolResult, MCPToolSpec


class LocalMCPAdapter:
    """MCP-like local adapter exposing ShotForge capabilities as tools/resources."""

    def __init__(self, knowledge_base: KnowledgeBase | None = None):
        self.knowledge_base = knowledge_base or KnowledgeBase()
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
                description="Read harness audit data for a run id.",
                input_schema={"run_id": "string"},
                output_schema={"harness_audit": "object"},
            ),
        }

    def server_info(self) -> MCPServerInfo:
        return MCPServerInfo(
            capabilities=[
                "tools/list",
                "tools/call",
                "resources/list",
                "resources/read",
                "shotforge/run-audit",
            ]
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "server": self.server_info().model_dump(mode="json"),
            "tools": [tool.model_dump(mode="json") for tool in self.list_tools()],
            "resources": [resource.model_dump(mode="json") for resource in self.list_resources()],
        }

    def list_tools(self) -> list[MCPToolSpec]:
        return list(self._tools.values())

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> MCPToolResult:
        arguments = arguments or {}
        if name not in self._tools:
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
            return MCPToolResult(tool_name=name, result={"items": items})
        if name == "runs.list":
            return MCPToolResult(tool_name=name, result={"run_ids": self._list_runs(arguments)})
        try:
            if name == "runs.get_package":
                return MCPToolResult(tool_name=name, result={"package": self._get_package(arguments)})
            if name == "runs.get_harness_audit":
                package = self._get_package(arguments)
                state = ProjectState.model_validate(package)
                return MCPToolResult(
                    tool_name=name,
                    result={"harness_audit": build_harness_audit(state)},
                )
        except Exception as exc:
            return MCPToolResult(
                tool_name=name,
                status="failed",
                is_error=True,
                error=str(exc),
            )
        return MCPToolResult(tool_name=name, result={})

    def list_resources(self) -> list[MCPResourceSpec]:
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
                        name=f"{run_id} harness audit",
                        description="ShotForge harness audit JSON",
                        metadata={"run_id": run_id, "kind": "harness_audit"},
                    ),
                ]
            )
        return resources

    def read_resource(self, uri: str) -> dict[str, Any]:
        prefix = "shotforge://runs/"
        if not uri.startswith(prefix):
            raise ValueError(f"Unsupported resource uri: {uri}")
        if uri.endswith("/package"):
            run_id = uri[len(prefix) : -len("/package")]
            return self._read_package(run_id)
        if uri.endswith("/harness"):
            run_id = uri[len(prefix) : -len("/harness")]
            return build_harness_audit(ProjectState.model_validate(self._read_package(run_id)))
        raise ValueError(f"Unsupported resource uri: {uri}")

    def _list_runs(self, arguments: dict[str, Any]) -> list[str]:
        limit = int(arguments.get("limit", 20))
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


def build_default_mcp_adapter() -> LocalMCPAdapter:
    return LocalMCPAdapter()
