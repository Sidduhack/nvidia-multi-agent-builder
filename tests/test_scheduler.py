from uuid import uuid4

import pytest

from app.agents.definitions import AgentDefinition, AgentRegistry
from app.agents.executor import AgentExecutor
from app.events.bus import EventBus
from app.memory.project import ProjectMemory
from app.models.registry import Capability, ModelProfile, ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.graph import TaskGraph
from app.orchestrator.scheduler import Scheduler
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse
from app.schemas.task import AgentTask, TaskStatus


class Provider(AIProvider):
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(model=request.model, content='{"summary":"done"}')

    async def stream(self, request: CompletionRequest):
        if False:
            yield ""

    async def list_models(self) -> list[str]:
        return []


@pytest.mark.asyncio
async def test_scheduler_runs_only_ready_tasks() -> None:
    project_id = uuid4()
    first = AgentTask(project_id=project_id, agent="planner", objective="plan")
    second = AgentTask(project_id=project_id, agent="planner", objective="next", dependencies=[first.id])
    graph = TaskGraph()
    graph.add(first)
    graph.add(second)

    agents = AgentRegistry()
    agents.register(AgentDefinition(name="planner", description="p", system_prompt="p", required_capabilities={Capability.PLANNING}))
    models = ModelRegistry()
    models.register(ModelProfile(model_id="test", capabilities={Capability.PLANNING}))
    events = EventBus()
    scheduler = Scheduler(graph, agents, AgentExecutor(Provider(), ModelRouter(models)), ProjectMemory(), events)

    ran = await scheduler.run_ready()
    assert [task.id for task in ran] == [first.id]
    assert first.status == TaskStatus.COMPLETED
    assert second.status == TaskStatus.PENDING
    await scheduler.run_ready()
    assert second.status == TaskStatus.COMPLETED
    assert [event.type for event in events.history].count("TASK_COMPLETED") == 2
