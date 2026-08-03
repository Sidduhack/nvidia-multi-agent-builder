from __future__ import annotations

from dataclasses import dataclass

from app.agent_catalog import AgentDefinition, get_agent
from app.performance import PerformanceController
from app.providers.base import AIProvider, ChatMessage, CompletionRequest, CompletionResponse


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    agent_id: str
    model: str
    content: str
    usage: dict[str, object]


class AgentExecutionService:
    """Canonical boundary between specialist agents and an AI provider."""

    def __init__(
        self,
        provider: AIProvider,
        *,
        default_model: str,
        performance: PerformanceController | None = None,
    ) -> None:
        if not default_model.strip():
            raise ValueError("default_model must not be empty")
        self._provider = provider
        self._default_model = default_model.strip()
        self._performance = performance or PerformanceController()

    async def execute(
        self,
        agent_id: str,
        task: str,
        *,
        model: str | None = None,
    ) -> AgentExecutionResult:
        if not task.strip():
            raise ValueError("task must not be empty")
        agent = get_agent(agent_id)
        selected_model = (model or self._default_model).strip()
        if not selected_model:
            raise ValueError("model must not be empty")

        async def operation() -> CompletionResponse:
            return await self._provider.complete(
                CompletionRequest(
                    model=selected_model,
                    messages=self._messages(agent, task.strip()),
                )
            )

        response = await self._performance.run(operation)
        return AgentExecutionResult(
            agent_id=agent.agent_id,
            model=response.model,
            content=response.content,
            usage=dict(response.usage),
        )

    @staticmethod
    def _messages(agent: AgentDefinition, task: str) -> list[ChatMessage]:
        return [
            ChatMessage(
                role="system",
                content=(
                    f"You are the {agent.display_name} specialist. "
                    f"Your responsibility is: {agent.purpose} "
                    "Work only on the assigned task. Return concise implementation output; "
                    "do not claim tools, tests, files, or external actions that did not occur."
                ),
            ),
            ChatMessage(role="user", content=task),
        ]

    def performance_snapshot(self):
        return self._performance.snapshot()
