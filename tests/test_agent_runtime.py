from uuid import uuid4

import pytest

from app.agents.definitions import default_agent_registry
from app.events.bus import EventBus, ProjectEvent
from app.memory.project import ProjectMemory
from app.models.discovery import ModelDiscovery
from app.models.registry import ModelRegistry
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse


class FakeProvider(AIProvider):
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(model=request.model, content='{"summary":"ok"}')

    async def stream(self, request: CompletionRequest):
        if False:
            yield ""

    async def list_models(self) -> list[str]:
        return ["model-a", "model-b"]


def test_default_agents_are_specialized() -> None:
    registry = default_agent_registry()
    assert registry.get("planner").name == "planner"
    assert registry.get("architect").name == "architect"
    assert registry.get("planner").system_prompt != registry.get("architect").system_prompt


def test_project_memory_returns_only_requested_categories() -> None:
    project_id = uuid4()
    memory = ProjectMemory()
    memory.append(project_id, "requirements", {"name": "demo"})
    memory.append(project_id, "secret-unrelated-context", "not requested")
    assert memory.context(project_id, ["requirements"]) == {"requirements": [{"name": "demo"}]}


@pytest.mark.asyncio
async def test_event_bus_records_events() -> None:
    event_bus = EventBus()
    event = ProjectEvent(project_id=uuid4(), type="TASK_CREATED")
    await event_bus.publish(event)
    assert event_bus.history == [event]


@pytest.mark.asyncio
async def test_discovery_does_not_invent_model_capabilities() -> None:
    registry = ModelRegistry()
    profiles = await ModelDiscovery(FakeProvider(), registry).refresh()
    assert {profile.model_id for profile in profiles} == {"model-a", "model-b"}
    assert all(not profile.enabled for profile in profiles)
    assert all(profile.capabilities == set() for profile in profiles)
