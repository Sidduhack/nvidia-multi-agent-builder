from collections.abc import AsyncIterator

import pytest

from app.execution import AgentExecutionService
from app.model_registry import MINIMAX_M3
from app.orchestrator import MultiAgentOrchestrator
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse


class PrimaryFailureProvider(AIProvider):
    """Fail MiniMax deliberately and let every other candidate succeed."""

    def __init__(self) -> None:
        self.models: list[str] = []

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.models.append(request.model)
        if request.model == MINIMAX_M3:
            raise RuntimeError("simulated primary model outage")
        return CompletionResponse(
            model=request.model,
            content=f"completed by {request.model}",
            usage={"simulated": True},
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        if False:
            yield request.model

    async def list_models(self) -> list[str]:
        return []


class PreferredModels:
    def model_for_agent(self, agent_id: str) -> str:
        return f"preferred/{agent_id}"


@pytest.mark.asyncio
async def test_full_orchestrator_continues_after_primary_model_failure() -> None:
    provider = PrimaryFailureProvider()
    runner = AgentExecutionService(provider, default_model="test/default")
    orchestrator = MultiAgentOrchestrator(runner, PreferredModels(), max_parallel_agents=1)

    result = await orchestrator.execute(
        "Build a small production-ready calculator website.",
        "Implement the calculator with concise specialist contributions.",
    )

    frontend = next(item for item in result.specialist_results if item.agent_id == "frontend")
    integration = next(item for item in result.specialist_results if item.agent_id == "integration")

    # Both routes deliberately start on MiniMax M3. The fake provider rejects it.
    # Health-aware routing may then choose any healthy verified fallback based on
    # runtime observations, so this integration test asserts behavior rather than
    # coupling itself to one static fallback position.
    assert frontend.model != MINIMAX_M3
    assert integration.model != MINIMAX_M3
    assert result.review.content

    # Prove the failed primary was actually attempted and that orchestration still
    # reached successful fallback models plus the reviewer instead of aborting.
    assert MINIMAX_M3 in provider.models
    assert any(model != MINIMAX_M3 for model in provider.models)
    assert result.review.agent_id == "reviewer"
    assert len(result.specialist_results) == 11
