from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Protocol


class SandboxViolation(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    allowed_executables: frozenset[str] = field(
        default_factory=lambda: frozenset({"python", "python3", "pytest", "npm", "npx", "node"})
    )
    denied_arguments: frozenset[str] = field(
        default_factory=lambda: frozenset({"--privileged", "--network=host", "--pid=host"})
    )
    max_timeout_seconds: float = 300.0
    max_output_bytes: int = 100_000
    network_enabled: bool = False
    read_only_root: bool = True
    max_memory_mb: int = 512
    max_processes: int = 64


@dataclass(frozen=True, slots=True)
class SandboxRequest:
    command: tuple[str, ...]
    workspace: str
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str


class SandboxBackend(Protocol):
    async def execute(self, request: SandboxRequest, policy: SandboxPolicy) -> SandboxResult: ...


class SecureSandboxExecutor:
    """Policy gate for a future container backend; never invokes a host shell itself."""

    _drive_pattern = re.compile(r"^[A-Za-z]:")

    def __init__(self, backend: SandboxBackend, policy: SandboxPolicy | None = None) -> None:
        self.backend = backend
        self.policy = policy or SandboxPolicy()

    @classmethod
    def _workspace(cls, raw: str) -> str:
        value = raw.strip().replace("\\", "/")
        if not value or value.startswith("/") or cls._drive_pattern.match(value):
            raise SandboxViolation("Workspace must be a relative project path")
        path = PurePosixPath(value)
        if any(part in {"", ".", ".."} for part in path.parts):
            raise SandboxViolation("Unsafe workspace path")
        return path.as_posix()

    def validate(self, request: SandboxRequest) -> SandboxRequest:
        if not request.command:
            raise SandboxViolation("Command cannot be empty")
        executable = request.command[0]
        if executable not in self.policy.allowed_executables:
            raise SandboxViolation("Executable is not allowed")
        if any(argument in self.policy.denied_arguments for argument in request.command[1:]):
            raise SandboxViolation("Command contains a denied argument")
        if request.timeout_seconds <= 0 or request.timeout_seconds > self.policy.max_timeout_seconds:
            raise SandboxViolation("Execution timeout exceeds policy")
        return SandboxRequest(
            command=request.command,
            workspace=self._workspace(request.workspace),
            timeout_seconds=request.timeout_seconds,
        )

    def _bounded(self, value: str) -> str:
        encoded = value.encode("utf-8")
        if len(encoded) <= self.policy.max_output_bytes:
            return value
        return encoded[: self.policy.max_output_bytes].decode("utf-8", errors="ignore") + "\n...[output truncated]"

    async def run(self, command: tuple[str, ...], timeout_seconds: float) -> tuple[int, str, str]:
        request = self.validate(
            SandboxRequest(command=command, workspace="project", timeout_seconds=timeout_seconds)
        )
        result = await self.backend.execute(request, self.policy)
        return result.exit_code, self._bounded(result.stdout), self._bounded(result.stderr)
