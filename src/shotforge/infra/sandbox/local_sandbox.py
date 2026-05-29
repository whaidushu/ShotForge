from __future__ import annotations

import os
import subprocess
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, Field

from shotforge.infra.sandbox.policy import SandboxPolicy


class SandboxResult(BaseModel):
    command: list[str]
    status: str
    profile_id: str = ""
    policy_decision: str = "allowed"
    policy_reason: str = ""
    working_dir: str = ""
    allowed_env_keys: list[str] = Field(default_factory=list)
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    timed_out: bool = False
    artifacts: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class LocalSandboxRunner:
    """Policy gate for local command execution. This is not container isolation."""

    def __init__(self, policy: SandboxPolicy | None = None):
        self.policy = policy or SandboxPolicy()

    def run(
        self,
        command: list[str],
        timeout_seconds: int | None = None,
        *,
        raise_on_policy_violation: bool = True,
    ) -> SandboxResult:
        started = perf_counter()
        decision, reason = self._policy_decision(command, timeout_seconds)
        if decision != "allowed":
            result = self._result(
                command,
                status="denied",
                started=started,
                policy_decision=decision,
                policy_reason=reason,
            )
            if raise_on_policy_violation:
                raise PermissionError(reason)
            return result
        if self.policy.dry_run:
            return self._result(
                command=command,
                status="dry_run",
                started=started,
                policy_decision="allowed",
                policy_reason="dry_run_enabled",
            )

        env = {key: os.environ[key] for key in self.policy.allowed_env_keys if key in os.environ}
        try:
            completed = subprocess.run(
                command,
                cwd=self.policy.working_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds or self.policy.max_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return self._result(
                command=command,
                status="timeout",
                started=started,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                timed_out=True,
                policy_reason="timeout_expired",
            )

        return self._result(
            command=command,
            status="completed" if completed.returncode == 0 else "failed",
            started=started,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            policy_reason="process_completed",
        )

    def _policy_decision(self, command: list[str], timeout_seconds: int | None) -> tuple[str, str]:
        if not command:
            return "denied", "Sandbox command cannot be empty."
        executable = command[0].lower()
        allowed = {item.lower() for item in self.policy.allowed_commands}
        if executable not in allowed:
            return "denied", f"Command is not allowed by sandbox policy: {command[0]}"
        if timeout_seconds and timeout_seconds > self.policy.max_timeout_seconds:
            return "denied", "Requested timeout exceeds sandbox policy."
        return "allowed", "policy_matched"

    def _result(
        self,
        command: list[str],
        *,
        status: str,
        started: float,
        policy_decision: str = "allowed",
        policy_reason: str = "",
        exit_code: int | None = None,
        stdout: str = "",
        stderr: str = "",
        timed_out: bool = False,
    ) -> SandboxResult:
        return SandboxResult(
            command=command,
            status=status,
            profile_id=self.policy.execution_profile.profile_id,
            policy_decision=policy_decision,
            policy_reason=policy_reason,
            working_dir=str(self.policy.working_dir),
            allowed_env_keys=self.policy.allowed_env_keys,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=(perf_counter() - started) * 1000,
            timed_out=timed_out,
            artifacts=self._artifact_manifest(),
            metadata={"policy": self.policy.model_dump(mode="json")},
        )

    def _artifact_manifest(self) -> list[str]:
        profile = self.policy.execution_profile
        if not profile.capture_artifacts:
            return []
        root = Path(self.policy.working_dir)
        if not root.exists():
            return []
        artifacts: list[str] = []
        for pattern in profile.artifact_globs:
            artifacts.extend(str(path) for path in root.glob(pattern) if path.is_file())
        return sorted(set(artifacts))
