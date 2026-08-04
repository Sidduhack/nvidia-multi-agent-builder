from collections.abc import AsyncIterator

import pytest

from app.execution import AgentExecutionService, ModelFallbackError
from app.model_health import ModelHealthRegistry
from app.model_registry import DEEPSEEK_V4_PRO, MINIMAX_M3, NEMOTRON_SUPER
from app.performance import PerformanceController, PerformanceLimits
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse


class FakeProvider(AIProvider):
    def __init__(self, *, failing_models: set[str] | None = None) -> None:
        self.requests: list[CompletionRequest] = []
        self.failing_models = failing_models or set()

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        if request.model in self.failing_models:
            raise RuntimeError(f"provider failed for {request.model}")
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
    assert result.model == NEMOTRON_SUPER
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


@pytest.mark.asyncio
async def test_execution_falls_back_when_primary_model_fails() -> None:
    provider = FakeProvider(failing_models={MINIMAX_M3})
    service = AgentExecutionService(provider, default_model="test/default")

    result = await service.execute("frontend", "Implement a concise frontend.")

    assert result.model != MINIMAX_M3
    assert [request.model for request in provider.requests][:2] == [
        MINIMAX_M3,
        DEEPSEEK_V4_PRO,
    ]


@pytest.mark.asyncio
async def test_execution_uses_later_fallback_after_multiple_failures() -> None:
    provider = FakeProvider(failing_models={MINIMAX_M3, DEEPSEEK_V4_PRO})
    service = AgentExecutionService(provider, default_model="test/default")

    result = await service.execute("frontend", "Implement a concise frontend.")

    assert result.model == NEMOTRON_SUPER
    assert [request.model for request in provider.requests] == [
        MINIMAX_M3,
        DEEPSEEK_V4_PRO,
        NEMOTRON_SUPER,
    ]


@pytest.mark.asyncio
async def test_execution_raises_after_all_model_candidates_fail() -> None:
    provider = FakeProvider(
        failing_models={MINIMAX_M3, DEEPSEEK_V4_PRO, NEMOTRON_SUPER}
    )
    service = AgentExecutionService(provider, default_model="test/default")

    with pytest.raises(ModelFallbackError) as caught:
        await service.execute("frontend", "Implement a concise frontend.")

    assert caught.value.agent_id == "frontend"
    assert len(caught.value.failures) == 3
    assert [request.model for request in provider.requests] == [
        MINIMAX_M3,
        DEEPSEEK_V4_PRO,
        NEMOTRON_SUPER,
    ]


@pytest.mark.asyncio
async def test_explicit_model_failure_does_not_fallback() -> None:
    provider = FakeProvider(failing_models={"test/override"})
    service = AgentExecutionService(provider, default_model="test/default")

    with pytest.raises(ModelFallbackError):
        await service.execute(
            "frontend",
            "Implement a concise frontend.",
            model="test/override",
        )

    assert [request.model for request in provider.requests] == ["test/override"]


@pytest.mark.asyncio
async def test_execution_records_model_success_health() -> None:
    provider = FakeProvider()
    health = ModelHealthRegistry()
    service = AgentExecutionService(provider, default_model="test/default", model_health=health)

    result = await service.execute("frontend", "Implement a concise frontend.")
    model_health = health.get(result.model)

    assert model_health.success_count == 1
    assert model_health.failure_count == 0
    assert model_health.average_latency_seconds is not None


@pytest.mark.asyncio
async def test_execution_records_failure_then_fallback_success() -> None:
    provider = FakeProvider(failing_models={MINIMAX_M3})
    health = ModelHealthRegistry()
    service = AgentExecutionService(provider, default_model="test/default", model_health=health)

    result = await service.execute("frontend", "Implement a concise frontend.")

    assert result.model == DEEPSEEK_V4_PRO
    assert health.get(MINIMAX_M3).failure_count == 1
    assert health.get(DEEPSEEK_V4_PRO).success_count == 1


@pytest.mark.asyncio
async def test_execution_reorders_future_requests_away_from_degraded_primary() -> None:
    provider = FakeProvider(failing_models={MINIMAX_M3})
    health = ModelHealthRegistry(failure_threshold=2)
    service = AgentExecutionService(provider, default_model="test/default", model_health=health)

    first = await service.execute("frontend", "Implement the first frontend task.")
    assert first.model == DEEPSEEK_V4_PRO
    first_request_count = len(provider.requests)

    second = await service.execute("frontend", "Implement the second frontend task.")
    second_models = [request.model for request in provider.requests[first_request_count:]]

    assert second.model == DEEPSEEK_V4_PRO
    assert second_models == [DEEPSEEK_V4_PRO]
    assert health.get(MINIMAX_M3).failure_count == 1


@pytest.mark.asyncio
async def test_explicit_model_override_ignores_health_reordering() -> None:
    provider = FakeProvider()
    health = ModelHealthRegistry(failure_threshold=1)
    health.record_failure("test/override")
    service = AgentExecutionService(provider, default_model="test/default", model_health=health)

    result = await service.execute(
        "frontend",
        "Implement a concise frontend.",
        model="test/override",
    )

    assert result.model == "test/override"
    assert [request.model for request in provider.requests] == ["test/override"]
