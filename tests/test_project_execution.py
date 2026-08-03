import pytest

from app.api.projects import ProjectCreate, ProjectStatus, ProjectStore
from app.execution import AgentExecutionResult
from app.project_execution import ProjectExecutionService


class FakeRunner:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str, str | None]] = []

    async def execute(
        self,
        agent_id: str,
        task: str,
        *,
        model: str | None = None,
    ) -> AgentExecutionResult:
        self.calls.append((agent_id, task, model))
        if self.fail:
            raise RuntimeError("provider failed")
        return AgentExecutionResult(
            agent_id=agent_id,
            model=model or "test/default",
            content="planner output",
            usage={},
        )


class FakeModels:
    def model_for_agent(self, agent_id: str) -> str:
        return f"test/{agent_id}"


@pytest.mark.asyncio
async def test_start_runs_planner_and_advances_project() -> None:
    store = ProjectStore()
    project = store.create(
        ProjectCreate(
            name="Demo project",
            prompt="Build a sufficiently detailed full-stack demonstration application.",
        )
    )
    runner = FakeRunner()
    service = ProjectExecutionService(store, runner, FakeModels())

    result = await service.start(project.id)

    assert result.planner_output == "planner output"
    assert store.get(project.id).status is ProjectStatus.RUNNING  # type: ignore[union-attr]
    assert runner.calls[0][0] == "planner"
    assert runner.calls[0][2] == "test/planner"
    assert "Demo project" in runner.calls[0][1]


@pytest.mark.asyncio
async def test_start_marks_project_failed_when_planner_fails() -> None:
    store = ProjectStore()
    project = store.create(
        ProjectCreate(
            name="Failing project",
            prompt="Build a sufficiently detailed application that exercises failure handling.",
        )
    )
    service = ProjectExecutionService(store, FakeRunner(fail=True), FakeModels())

    with pytest.raises(RuntimeError, match="provider failed"):
        await service.start(project.id)

    assert store.get(project.id).status is ProjectStatus.FAILED  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_start_rejects_duplicate_execution() -> None:
    store = ProjectStore()
    project = store.create(
        ProjectCreate(
            name="Single start",
            prompt="Build a sufficiently detailed project and prevent duplicate execution starts.",
        )
    )
    runner = FakeRunner()
    service = ProjectExecutionService(store, runner, FakeModels())

    await service.start(project.id)

    with pytest.raises(ValueError, match="cannot start"):
        await service.start(project.id)

    assert len(runner.calls) == 1
