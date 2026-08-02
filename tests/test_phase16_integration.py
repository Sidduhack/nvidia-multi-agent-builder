from app.sandbox import SandboxPolicy, SandboxRequest, SandboxResult, SecureSandboxExecutor
from app.security_review import SecurityReviewer
from app.testing import TestCase, TestKind, TestRunner, TestStatus
from app.workspace import Workspace


class PassingSandboxBackend:
    async def execute(self, request: SandboxRequest, policy: SandboxPolicy) -> SandboxResult:
        assert policy.network_enabled is False
        assert policy.read_only_root is True
        return SandboxResult(exit_code=0, stdout="tests passed", stderr="")


async def test_workspace_security_and_testing_pipeline() -> None:
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
    security_report = SecurityReviewer().scan_project(files)
    assert security_report.blocking is False

    sandbox = SecureSandboxExecutor(PassingSandboxBackend())
    runner = TestRunner(sandbox)
    result = await runner.run_case(
        TestCase(
            id="integration-001",
            name="Generated project tests",
            kind=TestKind.INTEGRATION,
            command=("pytest", "-q"),
            timeout_seconds=30,
        )
    )
    assert result.status is TestStatus.PASSED
    assert result.stdout == "tests passed"


async def test_security_gate_blocks_project_before_execution() -> None:
    workspace = Workspace()
    workspace.write(
        "backend/config.py",
        'API_KEY = "this-is-a-real-looking-secret"\n',
        agent="backend",
        task_id="backend-002",
        reason="Unsafe generated configuration",
    )

    files = {record.path: record.content for record in workspace.list_files()}
    report = SecurityReviewer().scan_project(files)
    assert report.blocking is True
    assert any(finding.rule_id == "SEC001" for finding in report.findings)


def test_workspace_revision_conflict_protects_integration_state() -> None:
    workspace = Workspace()
    first = workspace.write(
        "frontend/src/App.tsx",
        "v1",
        agent="frontend",
        task_id="frontend-001",
        reason="Initial UI",
    )
    assert first.revision == 1

    updated = workspace.write(
        "frontend/src/App.tsx",
        "v2",
        agent="integrator",
        task_id="integration-001",
        reason="Approved integration change",
        expected_revision=1,
    )
    assert updated.revision == 2
    assert workspace.read("frontend/src/App.tsx").content == "v2"
