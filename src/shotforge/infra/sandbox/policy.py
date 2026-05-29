from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class SandboxExecutionProfile(BaseModel):
    profile_id: str = "local_python_readonly"
    description: str = "Local Python execution profile with constrained environment."
    capture_artifacts: bool = True
    artifact_globs: list[str] = Field(default_factory=lambda: ["*.json", "*.csv", "*.md", "*.log"])
    metadata: dict = Field(default_factory=dict)


class SandboxPolicy(BaseModel):
    sandbox_id: str = "local_command_sandbox"
    dry_run: bool = True
    allowed_commands: list[str] = Field(default_factory=lambda: ["python"])
    working_dir: Path = Field(default_factory=Path.cwd)
    max_timeout_seconds: int = 30
    allowed_env_keys: list[str] = Field(default_factory=list)
    allow_network: bool = False
    allow_file_write: bool = False
    execution_profile: SandboxExecutionProfile = Field(default_factory=SandboxExecutionProfile)
    metadata: dict = Field(default_factory=dict)
