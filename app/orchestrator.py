from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from app.execution import AgentExecutionResult


class AgentRunner(Protocol):
    async def execute(
        self,
        agent_id: str,
        task: str,
        *,
        model: str | None = None,
    ) -> AgentExecutionResult: ...


class ModelResolver(Protocol):
    def model_for_agent(self, agent_id: str) -> str: ...


SPECIALIST_AGENTS = (
    "architect",
    "ui-ux",
    "frontend",
    "backend",
    "database",
    "sound-engineer",
    "security",
    "testing",
    "performance",
    "integration",
    "debugging",
)


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    specialist_results: tuple[AgentExecutionResult, ...]
    review: AgentExecutionResult


class MultiAgentOrchestrator:
    """Coordinate specialist execution from an approved planner output."""

    def __init__(
        self,
        runner: AgentRunner,
        model_resolver: ModelResolver,
        *,
        max_parallel_agents: int = 2,
    ) -> None:
        if max_parallel_agents < 1:
            raise ValueError("max_parallel_agents must be positive")
        self._runner = runner
        self._model_resolver = model_resolver
        self._semaphore = asyncio.Semaphore(max_parallel_agents)

    async def execute(self, project_prompt: str, planner_output: str) -> OrchestrationResult:
        if not project_prompt.strip():
            raise ValueError("project_prompt must not be empty")
        if not planner_output.strip():
            raise ValueError("planner_output must not be empty")

        async def run_specialist(agent_id: str) -> AgentExecutionResult:
            async with self._semaphore:
                return await self._runner.execute(
                    agent_id,
                    self._specialist_task(agent_id, project_prompt, planner_output),
                    model=self._model_resolver.model_for_agent(agent_id),
                )

        specialist_results = tuple(
            await asyncio.gather(*(run_specialist(agent_id) for agent_id in SPECIALIST_AGENTS))
        )
        review = await self._runner.execute(
            "reviewer",
            self._review_task(project_prompt, planner_output, specialist_results),
            model=self._model_resolver.model_for_agent("reviewer"),
        )
        return OrchestrationResult(specialist_results=specialist_results, review=review)

    @staticmethod
    def _specialist_task(agent_id: str, project_prompt: str, planner_output: str) -> str:
        return (
            f"Original project request:\n{project_prompt}\n\n"
            f"Planner output:\n{planner_output}\n\n"
            f"Act as the {agent_id} specialist. Produce your concrete contribution for this project. "
            "Stay within your specialty, identify assumptions, and provide implementation-ready output. "
            "Do not claim files, tests, commands, deployments, or external actions were performed."
        )

    @staticmethod
    def _review_task(
        project_prompt: str,
        planner_output: str,
        results: tuple[AgentExecutionResult, ...],
    ) -> str:
        sections = "\n\n".join(
            f"## {result.agent_id}\n{result.content}" for result in results
        )
        return (
            f"Original project request:\n{project_prompt}\n\n"
            f"Planner output:\n{planner_output}\n\n"
            f"Specialist outputs:\n{sections}\n\n"
            "Review the combined specialist work for contradictions, missing requirements, unsafe choices, "
            "integration problems, and implementation gaps. Produce a prioritized final integration brief. "
            "Do not claim implementation or verification occurred unless the supplied outputs prove it."
        )
