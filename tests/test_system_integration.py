from app.sandbox import SandboxPolicy, SandboxRequest, SandboxResult, SecureSandboxExecutor
from app.security_review import SecurityReviewer
from app.testing import TestCase, TestKind, TestRunner, TestStatus
from app.workspace import Workspace, WorkspaceError


class IntegrationSandboxBackend:
    async def execute(self, request: SandboxRequest, policy: SandboxPolicy) -> SandboxResult:
        if request.command[0] == "pytest":
            return SandboxResult(0, "2 passed", "")
        return SandboxResult(1, "", "unsupported test command")


async def test_workspace_security_sandbox_and_testing_pipeline() -> None:
    workspace = Workspace()
    workspace.write(
        "backend/app.py",
        "def health():\n    return {'status': 'ok'}\n",
        agent="backend",
        task_id="backend-001",
        reason="Create health endpoint",
    )
    workspace.write(
        "tests/test_app.py",
        "def test_health():\n    assert True\n",
        agent="testing",
        task_id="testing-001",
        reason="Verify health endpoint",
    )

    files = {record.path: record.content for record in workspace.list_files()}
    security = SecurityReviewer().scan_project(files)
    assert security.blocking is False

    sandbox = SecureSandboxExecutor(IntegrationSandboxBackend())
    runner = TestRunner(sandbox)
    result = await runner.run_case(
        TestCase("integration-001", "Generated project tests", TestKind.INTEGRATION, ("pytest", "-q"), 30)
    )

    assert result.status is TestStatus.PASSED
    assert result.exit_code == 0
    assert "passed" in result.stdout


async def test_security_gate_blocks_before_execution() -> None:
    workspace = Workspace()
    workspace.write(
        "backend/config.py",
        'API_KEY = "do-not-commit-this-secret"',
        agent="backend",
        task_id="backend-002",
        reason="Unsafe generated configuration",
    )

    files = {record.path: record.content for record in workspace.list_files()}
    report = SecurityReviewer().scan_project(files)

    assert report.blocking is True
    assert any(finding.rule_id == "SEC001" for finding in report.findings)


def test_workspace_conflict_protection_survives_integration_flow() -> None:
    workspace = Workspace()
    workspace.write(
        "frontend/src/App.tsx",
        "v1",
        agent="frontend",
        task_id="frontend-001",
        reason="Initial UI",
    )
    workspace.acquire("frontend/src/App.tsx", "frontend-001")

    try:
        workspace.write(
            "frontend/src/App.tsx",
            "conflicting change",
            agent="debugger",
            task_id="debug-001",
            reason="Unapproved concurrent repair",
        )
    except WorkspaceError as exc:
        assert "locked" in str(exc)
    else:
        raise AssertionError("Conflicting write should have been rejected")


async def test_sandbox_restrictions_apply_to_test_runner() -> None:
    sandbox = SecureSandboxExecutor(IntegrationSandboxBackend())
    runner = TestRunner(sandbox)
    result = await runner.run_case(
        TestCase("unsafe-001", "Unsafe command", TestKind.BUILD, ("bash", "-c", "id"), 10)
    )

    assert result.status is TestStatus.ERROR
    assert "SandboxViolation" in result.stderr
    assert "Executable is not allowed" not in result.stderr
