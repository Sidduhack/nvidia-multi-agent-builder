from app.sandbox import SandboxPolicy, SandboxRequest, SandboxResult, SecureSandboxExecutor
from app.security_review import SecurityReviewer
from app.testing import TestCase, TestKind, TestRunner, TestStatus
from app.workspace import Workspace


class PassingSandboxBackend:
    async def execute(self, request: SandboxRequest, policy: SandboxPolicy) -> SandboxResult:
        assert request.workspace == "project"
        assert policy.network_enabled is False
        assert policy.read_only_root is True
        return SandboxResult(0, "2 passed", "")


async def test_workspace_security_and_test_execution_pipeline() -> None:
    workspace = Workspace()
    workspace.write(
        "frontend/src/App.tsx",
        "export const App = () => <main>Safe</main>;",
        agent="frontend",
        task_id="frontend-001",
        reason="Create safe application shell",
    )
    workspace.write(
        "tests/test_app.py",
        "def test_app():\n    assert True\n",
        agent="testing",
        task_id="test-001",
        reason="Add smoke test",
    )

    files = {record.path: record.content for record in workspace.list_files()}
    security = SecurityReviewer().scan_project(files)
    assert security.blocking is False

    sandbox = SecureSandboxExecutor(PassingSandboxBackend())
    runner = TestRunner(sandbox)
    result = await runner.run_case(
        TestCase("suite-001", "Generated project tests", TestKind.INTEGRATION, ("pytest", "-q"), 30)
    )

    assert result.status is TestStatus.PASSED
    assert result.stdout == "2 passed"


async def test_security_gate_blocks_dangerous_project_before_execution() -> None:
    workspace = Workspace()
    workspace.write(
        "backend/config.py",
        'API_KEY = "hard-coded-secret-value"',
        agent="backend",
        task_id="backend-001",
        reason="Unsafe generated configuration",
    )

    files = {record.path: record.content for record in workspace.list_files()}
    report = SecurityReviewer().scan_project(files)

    assert report.blocking is True
    assert any(finding.rule_id == "SEC001" for finding in report.findings)


def test_workspace_revision_conflict_protects_integration_state() -> None:
    workspace = Workspace()
    workspace.write("README.md", "v1", agent="planner", task_id="p1", reason="initial")
    current = workspace.read("README.md")
    updated = workspace.write(
        "README.md",
        "v2",
        agent="integrator",
        task_id="i1",
        reason="approved integration",
        expected_revision=current.revision,
    )
    assert updated.revision == 2
    assert workspace.read("README.md").content == "v2"
