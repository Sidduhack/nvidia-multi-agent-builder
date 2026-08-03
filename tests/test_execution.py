from collections.abc import AsyncIterator

import pytest

from app.execution import AgentExecutionService
from app.performance import PerformanceController, PerformanceLimits
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse


class FakeProvider(AIProvider):
    def __init__(self) -> None:
        self.requests: list[CompletionRequest] = []

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        return CompletionResponse(model=request.model, content="implemented", usage={"calls": 1})

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        if False:
            yield request.model

    async def list_models(self) -> list[str]:
        return ["test/model"]


@pytest.mark.asyncio
async def test_execution_uses_registered_agent_and_provider() -> None:
    provider = FakeProvider()
    performance = PerformanceController(PerformanceLimits(max_parallel_agents=1))
    service = AgentExecutionService(
        provider,
        default_model="test/model",
        performance=performance,
    )

    result = await service.execute("sound-engineer", "Design accessible UI sound behavior.")

    assert result.agent_id == "sound-engineer"
    assert result.model == "test/model"
    assert result.content == "implemented"
    assert len(provider.requests) == 1
    messages = provider.requests[0].messages
    assert "Sound Engineer" in messages[0].content
    assert messages[1].content == "Design accessible UI sound behavior."
    snapshot = service.performance_snapshot()
    assert snapshot.completed == 1
    assert snapshot.failed == 0


@pytest.mark.asyncio
async def test_execution_rejects_unknown_agent_before_provider_call() -> None:
    provider = FakeProvider()
    service = AgentExecutionService(provider, default_model="test/model")

    with pytest.raises(KeyError, match="unknown agent"):
        await service.execute("not-real", "Do some valid task work here.")

    assert provider.requests == []


@pytest.mark.asyncio
async def test_execution_supports_explicit_model_override() -> None:
    provider = FakeProvider()
    service = AgentExecutionService(provider, default_model="test/default")

    result = await service.execute("planner", "Plan this sufficiently detailed project.", model="test/planner")

    assert result.model == "test/planner"
    assert provider.requests[0].model == "test/planner"
