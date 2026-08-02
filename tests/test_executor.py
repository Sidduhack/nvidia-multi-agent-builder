import pytest

from app.agents.definitions import AgentDefinition
from app.agents.executor import AgentExecutionError, AgentExecutor
from app.models.registry import Capability, ModelProfile, ModelRegistry
from app.models.router import ModelRouter
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse
from app.schemas.task import AgentTask
from uuid import uuid4


class OutputProvider(AIProvider):
    def __init__(self, content: str) -> None:
        self.content = content

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(model=request.model, content=self.content)

    async def stream(self, request: CompletionRequest):
        if False:
            yield ""

    async def list_models(self) -> list[str]:
        return []


def make_executor(content: str) -> AgentExecutor:
    registry = ModelRegistry()
    registry.register(
        ModelProfile(
            model_id="test-model",
            capabilities={Capability.PLANNING},
            enabled=True,
        )
    )
    return AgentExecutor(OutputProvider(content), ModelRouter(registry))


@pytest.mark.asyncio
async def test_executor_validates_json_contract() -> None:
    executor = make_executor('{"summary":"planned","decisions":["keep it small"]}')
    result = await executor.execute(
        AgentDefinition(
            name="planner",
            description="planner",
            system_prompt="plan",
            required_capabilities={Capability.PLANNING},
        ),
        AgentTask(project_id=uuid4(), agent="planner", objective="Plan project"),
        {},
    )
    assert result.summary == "planned"


@pytest.mark.asyncio
async def test_executor_rejects_unstructured_output() -> None:
    executor = make_executor("Here is my plan instead of JSON")
    with pytest.raises(AgentExecutionError):
        await executor.execute(
            AgentDefinition(
                name="planner",
                description="planner",
                system_prompt="plan",
                required_capabilities={Capability.PLANNING},
            ),
            AgentTask(project_id=uuid4(), agent="planner", objective="Plan project"),
            {},
        )
