from __future__ import annotations

from typing import Any, Protocol


class MCPToolProvider(Protocol):
    def list_tools(self) -> list[str]:
        """List available MCP tools."""

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool by name."""
