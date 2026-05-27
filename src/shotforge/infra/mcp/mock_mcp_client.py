from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MCPToolSpec(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MockMCPClient:
    def __init__(self):
        self._tools = {
            "knowledge.search": MCPToolSpec(
                name="knowledge.search",
                description="Mock MCP tool for searching external knowledge assets.",
                input_schema={"query": "string", "tags": "list[string]"},
                output_schema={"items": "list[object]"},
            ),
            "asset.resolve": MCPToolSpec(
                name="asset.resolve",
                description="Mock MCP tool for resolving generated media artifact references.",
                input_schema={"artifact_ref": "string"},
                output_schema={"uri": "string"},
            ),
        }

    def list_tools(self) -> list[MCPToolSpec]:
        return list(self._tools.values())

    def call_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"MCP tool not found: {name}")
        return {
            "tool": name,
            "status": "mocked",
            "payload": payload,
            "result": {},
        }


__all__ = ["MockMCPClient", "MCPToolSpec"]
