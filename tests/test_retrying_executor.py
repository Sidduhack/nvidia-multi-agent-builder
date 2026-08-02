from uuid import uuid4

import pytest

from app.agents.definitions import AgentDefinition
from app.agents.executor import AgentExecutor
from app.models.registry import Capability, ModelProfile, ModelRegistry
from app.models.router import ModelRouter
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse
from app.schemas.task import AgentTask


class FlakyProvider(AIProvider):
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary provider failure")
        return CompletionResponse(model=request.model, content='{"summary":"recovered"}')

    async def stream(self, request: CompletionRequest):
        if False:
            yield ""

    async def list_models(self) -> list[str]:
        return []


@pytest.mark.asyncio
async def test_executor_retries_provider_failure() -> None:
    models = ModelRegistry()
    models.register(ModelProfile(model_id="test", capabilities={Capability.PLANNING}))
    provider = FlakyProvider()
    executor = AgentExecutor(provider, ModelRouter(models))
    result = await executor.execute(
        AgentDefinition(
            name="planner",
            description="planner",
            system_prompt="plan",
            required_capabilities={Capability.PLANNING},
            max_retries=1,
        ),
        AgentTask(project_id=uuid4(), agent="planner", objective="plan"),
        {},
    )
    assert result.summary == "recovered"
    assert provider.calls == 2
