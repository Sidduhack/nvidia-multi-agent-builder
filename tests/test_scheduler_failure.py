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


class BrokenProvider(AIProvider):
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise RuntimeError("provider unavailable")

    async def stream(self, request: CompletionRequest):
        if False:
            yield ""

    async def list_models(self) -> list[str]:
        return []


@pytest.mark.asyncio
async def test_scheduler_records_failure_without_crashing_batch() -> None:
    task = AgentTask(project_id=uuid4(), agent="planner", objective="plan")
    graph = TaskGraph()
    graph.add(task)
    agents = AgentRegistry()
    agents.register(AgentDefinition(name="planner", description="p", system_prompt="p", required_capabilities={Capability.PLANNING}, max_retries=0))
    models = ModelRegistry()
    models.register(ModelProfile(model_id="test", capabilities={Capability.PLANNING}))
    events = EventBus()
    scheduler = Scheduler(graph, agents, AgentExecutor(BrokenProvider(), ModelRouter(models)), ProjectMemory(), events)
    await scheduler.run_ready()
    assert task.status == TaskStatus.FAILED
    assert events.history[-1].type == "TASK_FAILED"
    assert events.history[-1].payload["error_type"]
