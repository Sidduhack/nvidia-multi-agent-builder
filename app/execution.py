from __future__ import annotations

from dataclasses import dataclass

from app.agent_catalog import AgentDefinition, get_agent
from app.model_registry import route_for_agent
from app.performance import PerformanceController
from app.providers.base import AIProvider, ChatMessage, CompletionRequest, CompletionResponse


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    agent_id: str
    model: str
    content: str
    usage: dict[str, object]


class ModelFallbackError(RuntimeError):
    def __init__(self, agent_id: str, failures: tuple[tuple[str, Exception], ...]) -> None:
        self.agent_id = agent_id
        self.failures = failures
        attempted = ", ".join(model for model, _ in failures)
        super().__init__(f"all model candidates failed for {agent_id}: {attempted}")


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
        candidates = self._model_candidates(agent_id, model)
        failures: list[tuple[str, Exception]] = []

        for selected_model in candidates:
            async def operation(selected_model: str = selected_model) -> CompletionResponse:
                return await self._provider.complete(
                    CompletionRequest(
                        model=selected_model,
                        messages=self._messages(agent, task.strip()),
                    )
                )

            try:
                response = await self._performance.run(operation)
            except Exception as exc:  # noqa: BLE001 -- fallback requires provider failure capture
                failures.append((selected_model, exc))
                continue

            return AgentExecutionResult(
                agent_id=agent.agent_id,
                model=response.model,
                content=response.content,
                usage=dict(response.usage),
            )

        raise ModelFallbackError(agent_id, tuple(failures))

    def _model_candidates(self, agent_id: str, model: str | None) -> tuple[str, ...]:
        if model is not None:
            selected_model = model.strip()
            if not selected_model:
                raise ValueError("model must not be empty")
            return (selected_model,)
        return route_for_agent(agent_id, default_model=self._default_model).candidates

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
