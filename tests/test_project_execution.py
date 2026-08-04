import pytest

from app.checkpoints import CheckpointStore
from app.execution import AgentExecutionResult
from app.orchestrator import SPECIALIST_AGENTS
from app.project_execution import ProjectExecutionService
from app.project_store import ProjectCreate, ProjectStatus, ProjectStore


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
            content=f"{agent_id} output",
            usage={},
        )


class FailOnceRunner(FakeRunner):
    def __init__(self, fail_agent: str) -> None:
        super().__init__()
        self.fail_agent = fail_agent
        self.failed_once = False

    async def execute(
        self,
        agent_id: str,
        task: str,
        *,
        model: str | None = None,
    ) -> AgentExecutionResult:
        self.calls.append((agent_id, task, model))
        if agent_id == self.fail_agent and not self.failed_once:
            self.failed_once = True
            raise RuntimeError(f"{agent_id} failed once")
        return AgentExecutionResult(
            agent_id=agent_id,
            model=model or "test/default",
            content=f"{agent_id} output",
            usage={},
        )


class FakeModels:
    def model_for_agent(self, agent_id: str) -> str:
        return f"test/{agent_id}"


@pytest.mark.asyncio
async def test_start_runs_full_orchestration_and_completes_project() -> None:
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
    assert store.get(project.id).status is ProjectStatus.COMPLETED  # type: ignore[union-attr]
    assert runner.calls[0][0] == "planner"
    assert runner.calls[0][2] == "test/planner"
    assert "Demo project" in runner.calls[0][1]
    assert tuple(item.agent_id for item in result.orchestration.specialist_results) == SPECIALIST_AGENTS
    assert result.orchestration.review.agent_id == "reviewer"
    assert [call[0] for call in runner.calls] == ["planner", *SPECIALIST_AGENTS, "reviewer"]


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
async def test_start_rejects_duplicate_execution_without_extra_agent_calls() -> None:
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
    first_run_call_count = len(runner.calls)
    assert first_run_call_count == 1 + len(SPECIALIST_AGENTS) + 1

    with pytest.raises(ValueError, match="cannot start"):
        await service.start(project.id)

    assert len(runner.calls) == first_run_call_count


@pytest.mark.asyncio
async def test_failed_project_resumes_from_checkpoints_without_duplicate_calls() -> None:
    store = ProjectStore()
    checkpoints = CheckpointStore()
    project = store.create(
        ProjectCreate(
            name="Resumable project",
            prompt="Build a sufficiently detailed project and resume safely after a provider failure.",
        )
    )
    runner = FailOnceRunner("backend")
    service = ProjectExecutionService(
        store,
        runner,
        FakeModels(),
        max_parallel_agents=1,
        checkpoints=checkpoints,
    )

    with pytest.raises(RuntimeError, match="backend.*failed once"):
        await service.start(project.id)

    assert store.get(project.id).status is ProjectStatus.FAILED  # type: ignore[union-attr]
    first_run_agents = [call[0] for call in runner.calls]
    assert first_run_agents == ["planner", *SPECIALIST_AGENTS]

    saved = checkpoints.get(project.id)
    assert saved.planner is not None
    assert "backend" not in saved.specialists
    assert set(saved.specialists) == set(SPECIALIST_AGENTS) - {"backend"}
    assert saved.reviewer is None

    first_counts = {agent_id: first_run_agents.count(agent_id) for agent_id in set(first_run_agents)}

    result = await service.start(project.id)

    assert store.get(project.id).status is ProjectStatus.COMPLETED  # type: ignore[union-attr]
    all_agents = [call[0] for call in runner.calls]
    assert all_agents.count("planner") == first_counts["planner"] == 1
    for agent_id in SPECIALIST_AGENTS:
        expected = 2 if agent_id == "backend" else 1
        assert all_agents.count(agent_id) == expected
    assert all_agents.count("reviewer") == 1
    assert result.orchestration.review.agent_id == "reviewer"
    assert {run.agent_id for run in result.orchestration.runs if run.checkpointed} == (
        set(SPECIALIST_AGENTS) - {"backend"}
    )
