from __future__ import annotations

import os
import subprocess
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, Field

from shotforge.core.runtime_models import SandboxPolicyRecord
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
        self._policy_records: list[SandboxPolicyRecord] = []

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

    def policy_records(self) -> list[SandboxPolicyRecord]:
        return list(self._policy_records)

    def _policy_decision(self, command: list[str], timeout_seconds: int | None) -> tuple[str, str]:
        if not command:
            return "denied", "Sandbox command cannot be empty."
        executable = command[0].lower()
        allowed = {item.lower() for item in self.policy.allowed_commands}
        if executable not in allowed:
            return "denied", f"Command is not allowed by sandbox policy: {command[0]}"
        if timeout_seconds and timeout_seconds > self.policy.max_timeout_seconds:
            return "denied", "Requested timeout exceeds sandbox policy."
        boundary_decision = self._workspace_boundary_decision(command)
        if boundary_decision is not None:
            return "denied", boundary_decision
        if not self.policy.allow_network and self._looks_like_network_access(command):
            return "denied", "Network access is disabled by sandbox policy."
        if not self.policy.allow_file_write and self._looks_like_file_write(command):
            return "denied", "File writes are disabled by sandbox policy."
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
        result = SandboxResult(
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
        self._policy_records.append(
            SandboxPolicyRecord(
                command=command,
                decision="allowed" if policy_decision == "allowed" else "denied",
                reason=policy_reason,
                profile_id=result.profile_id,
                working_dir=result.working_dir,
                allow_network=self.policy.allow_network,
                allow_file_write=self.policy.allow_file_write,
                allowed_env_keys=self.policy.allowed_env_keys,
                artifacts=result.artifacts,
                metadata={
                    "status": status,
                    "exit_code": exit_code,
                    "timed_out": timed_out,
                    "sandbox_id": self.policy.sandbox_id,
                },
            )
        )
        return result

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
        bounded = []
        for artifact in sorted(set(artifacts)):
            path = Path(artifact).resolve()
            if self._path_within(path, root.resolve()):
                bounded.append(str(path))
        return bounded

    def _workspace_boundary_decision(self, command: list[str]) -> str | None:
        if not self.policy.require_workspace_boundary:
            return None
        working_dir = self.policy.working_dir.resolve()
        root = (self.policy.workspace_root or self.policy.working_dir).resolve()
        if not self._path_within(working_dir, root):
            return f"Working directory escapes sandbox workspace: {working_dir}"
        lowered = " ".join(command).lower()
        for fragment in self.policy.denied_path_fragments:
            if fragment.lower() in lowered:
                return f"Command references denied path fragment: {fragment}"
        return None

    def _looks_like_network_access(self, command: list[str]) -> bool:
        text = " ".join(command).lower()
        return any(marker in text for marker in ["http://", "https://", "curl ", "wget ", "invoke-webrequest"])

    def _looks_like_file_write(self, command: list[str]) -> bool:
        text = " ".join(command).lower()
        write_markers = [" > ", "set-content", "out-file", "tee ", "open(", "write_text", "remove-item"]
        return any(marker in text for marker in write_markers)

    def _path_within(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True
