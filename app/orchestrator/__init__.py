from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.execution import AgentExecutionResult

logger = logging.getLogger(__name__)


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
class AgentRunRecord:
    agent_id: str
    model: str
    elapsed_seconds: float
    result: AgentExecutionResult | None = None
    error: str | None = None
    checkpointed: bool = False


class OrchestrationError(RuntimeError):
    def __init__(self, failed: AgentRunRecord, completed: tuple[AgentRunRecord, ...]) -> None:
        self.failed = failed
        self.completed = completed
        super().__init__(
            f"agent {failed.agent_id} using {failed.model} failed after "
            f"{failed.elapsed_seconds:.1f}s: {failed.error}"
        )


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    specialist_results: tuple[AgentExecutionResult, ...]
    review: AgentExecutionResult
    runs: tuple[AgentRunRecord, ...] = ()


CheckpointCallback = Callable[[str, AgentExecutionResult], None]


class MultiAgentOrchestrator:
    """Coordinate specialists while allowing successful work to be resumed from checkpoints."""

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

    async def _run_agent(self, agent_id: str, task: str) -> AgentRunRecord:
        model = self._model_resolver.model_for_agent(agent_id)
        started = time.monotonic()
        logger.info("agent.start id=%s model=%s", agent_id, model)
        try:
            result = await self._runner.execute(agent_id, task, model=model)
        except Exception as exc:  # noqa: BLE001 -- agent failures are recorded, not suppressed
            elapsed = time.monotonic() - started
            logger.error(
                "agent.failed id=%s model=%s elapsed=%.1fs error=%s",
                agent_id,
                model,
                elapsed,
                exc,
            )
            return AgentRunRecord(agent_id, model, elapsed, error=str(exc))
        elapsed = time.monotonic() - started
        logger.info("agent.completed id=%s model=%s elapsed=%.1fs", agent_id, model, elapsed)
        return AgentRunRecord(agent_id, model, elapsed, result=result)

    async def execute(
        self,
        project_prompt: str,
        planner_output: str,
        *,
        completed_results: dict[str, AgentExecutionResult] | None = None,
        review_result: AgentExecutionResult | None = None,
        on_checkpoint: CheckpointCallback | None = None,
    ) -> OrchestrationResult:
        if not project_prompt.strip():
            raise ValueError("project_prompt must not be empty")
        if not planner_output.strip():
            raise ValueError("planner_output must not be empty")

        cached = completed_results or {}

        async def run_specialist(agent_id: str) -> AgentRunRecord:
            if agent_id in cached:
                result = cached[agent_id]
                return AgentRunRecord(
                    agent_id=agent_id,
                    model=result.model,
                    elapsed_seconds=0.0,
                    result=result,
                    checkpointed=True,
                )
            async with self._semaphore:
                record = await self._run_agent(
                    agent_id,
                    self._specialist_task(agent_id, project_prompt, planner_output),
                )
                if record.result is not None and on_checkpoint is not None:
                    on_checkpoint(agent_id, record.result)
                return record

        records = tuple(
            await asyncio.gather(*(run_specialist(agent_id) for agent_id in SPECIALIST_AGENTS))
        )
        completed = tuple(record for record in records if record.result is not None)
        failed = next((record for record in records if record.error is not None), None)
        if failed is not None:
            raise OrchestrationError(failed, completed)

        specialist_results = tuple(record.result for record in records if record.result is not None)

        if review_result is not None:
            review_record = AgentRunRecord(
                agent_id="reviewer",
                model=review_result.model,
                elapsed_seconds=0.0,
                result=review_result,
                checkpointed=True,
            )
        else:
            review_record = await self._run_agent(
                "reviewer",
                self._review_task(project_prompt, planner_output, specialist_results),
            )
            if review_record.result is None:
                raise OrchestrationError(review_record, completed)
            if on_checkpoint is not None:
                on_checkpoint("reviewer", review_record.result)

        return OrchestrationResult(
            specialist_results=specialist_results,
            review=review_record.result,
            runs=(*records, review_record),
        )

    @staticmethod
    def _specialist_task(agent_id: str, project_prompt: str, planner_output: str) -> str:
        return (
            f"Original project request:\n{project_prompt}\n\n"
            f"Planner output:\n{planner_output}\n\n"
            f"Act as the {agent_id} specialist. Produce your concrete contribution for this project. "
            "Stay within your specialty, identify assumptions, and provide implementation-ready output. "
            "Keep the response concise. Do not claim files, tests, commands, deployments, or external actions were performed."
        )

    @staticmethod
    def _review_task(
        project_prompt: str,
        planner_output: str,
        results: tuple[AgentExecutionResult, ...],
    ) -> str:
        sections = "\n\n".join(f"## {result.agent_id}\n{result.content}" for result in results)
        return (
            f"Original project request:\n{project_prompt}\n\n"
            f"Planner output:\n{planner_output}\n\n"
            f"Specialist outputs:\n{sections}\n\n"
            "Review the combined specialist work for contradictions, missing requirements, unsafe choices, "
            "integration problems, and implementation gaps. Produce a concise prioritized final integration brief. "
            "Do not claim implementation or verification occurred unless the supplied outputs prove it."
        )
