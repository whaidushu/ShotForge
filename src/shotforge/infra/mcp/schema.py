from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MCPServerInfo(BaseModel):
    name: str = "shotforge-local-mcp"
    version: str = "0.2.0"
    description: str = "Local MCP-like adapter for ShotForge tools and resources."
    capabilities: list[str] = Field(default_factory=list)


class MCPToolSpec(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPToolResult(BaseModel):
    tool_name: str
    status: str = "completed"
    result: dict[str, Any] = Field(default_factory=dict)
    is_error: bool = False
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPResourceSpec(BaseModel):
    uri: str
    name: str
    description: str = ""
    mime_type: str = "application/json"
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPPromptSpec(BaseModel):
    name: str
    description: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)
    template: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPAccessPolicy(BaseModel):
    policy_id: str = "default_mcp_access_policy"
    allowed_tools: list[str] = Field(default_factory=list)
    allowed_resource_prefixes: list[str] = Field(default_factory=lambda: ["shotforge://runs/"])
    expose_prompts: bool = True
    max_runs_list_limit: int = 50
    require_known_tool: bool = True
