import pytest

from app.sandbox import (
    SandboxPolicy,
    SandboxRequest,
    SandboxResult,
    SandboxViolation,
    SecureSandboxExecutor,
)


class FakeBackend:
    def __init__(self) -> None:
        self.last_policy: SandboxPolicy | None = None

    async def execute(self, request: SandboxRequest, policy: SandboxPolicy) -> SandboxResult:
        self.last_policy = policy
        return SandboxResult(0, "ok", "")


async def test_allowed_command_runs_through_backend() -> None:
    backend = FakeBackend()
    executor = SecureSandboxExecutor(backend)
    code, stdout, stderr = await executor.run(("pytest", "-q"), 30)
    assert (code, stdout, stderr) == (0, "ok", "")
    assert backend.last_policy is not None
    assert backend.last_policy.network_enabled is False
    assert backend.last_policy.read_only_root is True


@pytest.mark.parametrize("command", [("bash", "-c", "echo hi"), ("sh", "-c", "id"), ("curl", "example.com")])
def test_unapproved_executables_are_rejected(command: tuple[str, ...]) -> None:
    executor = SecureSandboxExecutor(FakeBackend())
    with pytest.raises(SandboxViolation, match="not allowed"):
        executor.validate(SandboxRequest(command, "project", 10))


def test_host_and_parent_paths_are_rejected() -> None:
    executor = SecureSandboxExecutor(FakeBackend())
    for workspace in ("../host", "/etc", "C:\\Users\\host"):
        with pytest.raises(SandboxViolation):
            executor.validate(SandboxRequest(("pytest",), workspace, 10))


def test_excessive_timeout_is_rejected() -> None:
    executor = SecureSandboxExecutor(FakeBackend(), SandboxPolicy(max_timeout_seconds=20))
    with pytest.raises(SandboxViolation, match="timeout"):
        executor.validate(SandboxRequest(("pytest",), "project", 21))


def test_denied_runtime_arguments_are_rejected() -> None:
    policy = SandboxPolicy(allowed_executables=frozenset({"docker"}))
    executor = SecureSandboxExecutor(FakeBackend(), policy)
    with pytest.raises(SandboxViolation, match="denied"):
        executor.validate(SandboxRequest(("docker", "run", "--privileged"), "project", 10))


async def test_output_is_bounded() -> None:
    class LoudBackend:
        async def execute(self, request: SandboxRequest, policy: SandboxPolicy) -> SandboxResult:
            return SandboxResult(0, "x" * 100, "y" * 100)

    executor = SecureSandboxExecutor(LoudBackend(), SandboxPolicy(max_output_bytes=10))
    _, stdout, stderr = await executor.run(("pytest",), 10)
    assert "truncated" in stdout
    assert "truncated" in stderr
