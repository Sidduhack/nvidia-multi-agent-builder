import asyncio

import pytest

from app.execution import AgentExecutionResult
from app.orchestrator import SPECIALIST_AGENTS, MultiAgentOrchestrator


class FakeSettings:
    def model_for_agent(self, agent_id: str) -> str:
        return f"test/{agent_id}"


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []
        self.active = 0
        self.peak_active = 0
        self.specialists_finished = 0
        self.reviewer_saw_all_specialists = False

    async def execute(self, agent_id: str, task: str, *, model: str | None = None) -> AgentExecutionResult:
        self.calls.append((agent_id, model))
        if agent_id == "reviewer":
            self.reviewer_saw_all_specialists = self.specialists_finished == len(SPECIALIST_AGENTS)
            return AgentExecutionResult(agent_id=agent_id, model=model or "test/reviewer", content="final integration review", usage={})

        self.active += 1
        self.peak_active = max(self.peak_active, self.active)
        await asyncio.sleep(0.01)
        self.active -= 1
        self.specialists_finished += 1
        return AgentExecutionResult(agent_id=agent_id, model=model or f"test/{agent_id}", content=f"{agent_id} contribution", usage={})


@pytest.mark.asyncio
async def test_orchestrator_runs_all_specialists_then_reviewer() -> None:
    runner = RecordingRunner()
    orchestrator = MultiAgentOrchestrator(runner, FakeSettings(), max_parallel_agents=3)
    result = await orchestrator.execute("Build a calculator application", "Planner says build it safely")

    assert tuple(item.agent_id for item in result.specialist_results) == SPECIALIST_AGENTS
    assert result.review.agent_id == "reviewer"
    assert runner.reviewer_saw_all_specialists is True
    assert runner.calls[-1][0] == "reviewer"


@pytest.mark.asyncio
async def test_orchestrator_respects_parallel_limit() -> None:
    runner = RecordingRunner()
    orchestrator = MultiAgentOrchestrator(runner, FakeSettings(), max_parallel_agents=2)
    await orchestrator.execute("Build a calculator application", "Planner says build it safely")
    assert runner.peak_active == 2


@pytest.mark.asyncio
async def test_orchestrator_delegates_model_routing_to_runner() -> None:
    runner = RecordingRunner()
    orchestrator = MultiAgentOrchestrator(runner, FakeSettings(), max_parallel_agents=4)
    result = await orchestrator.execute("Build a calculator application", "Planner says build it safely")

    # The orchestrator intentionally passes no explicit model. The execution
    # service can therefore try the verified primary/fallback route per agent.
    assert runner.calls == [
        *((agent_id, None) for agent_id in SPECIALIST_AGENTS),
        ("reviewer", None),
    ]
    assert [item.model for item in result.specialist_results] == [
        f"test/{agent_id}" for agent_id in SPECIALIST_AGENTS
    ]
    assert result.review.model == "test/reviewer"


@pytest.mark.asyncio
async def test_orchestrator_rejects_empty_inputs() -> None:
    runner = RecordingRunner()
    orchestrator = MultiAgentOrchestrator(runner, FakeSettings())

    with pytest.raises(ValueError, match="project_prompt"):
        await orchestrator.execute(" ", "valid planner output")
    with pytest.raises(ValueError, match="planner_output"):
        await orchestrator.execute("valid project prompt", " ")
    assert runner.calls == []
