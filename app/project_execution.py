from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.checkpoints import CheckpointStore, checkpoint_store
from app.execution import AgentExecutionResult
from app.orchestrator import MultiAgentOrchestrator, OrchestrationResult
from app.project_store import Project, ProjectStatus, ProjectStore


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


@dataclass(frozen=True, slots=True)
class ProjectExecutionResult:
    project_id: UUID
    planner_output: str
    orchestration: OrchestrationResult


class ProjectExecutionService:
    """Own project state transitions and resume successful AI work from checkpoints."""

    def __init__(
        self,
        store: ProjectStore,
        runner: AgentRunner,
        model_resolver: ModelResolver,
        *,
        max_parallel_agents: int = 2,
        checkpoints: CheckpointStore | None = None,
    ) -> None:
        self._store = store
        self._runner = runner
        self._model_resolver = model_resolver
        self._checkpoints = checkpoints or checkpoint_store
        self._orchestrator = MultiAgentOrchestrator(
            runner,
            model_resolver,
            max_parallel_agents=max_parallel_agents,
        )

    async def start(self, project_id: UUID) -> ProjectExecutionResult:
        project = self._require_project(project_id)
        if project.status not in (ProjectStatus.CREATED, ProjectStatus.FAILED):
            raise ValueError(f"project cannot start from status {project.status}")

        checkpoint = self._checkpoints.get(project_id)
        self._store.set_status(project_id, ProjectStatus.PLANNING)

        try:
            planner = checkpoint.planner
            if planner is None:
                # Let AgentExecutionService choose the verified planner route and
                # transparently fall back if the primary NVIDIA model fails.
                planner = await self._runner.execute(
                    "planner",
                    self._planner_task(project),
                )
                self._checkpoints.save_planner(project_id, planner)

            self._store.set_status(project_id, ProjectStatus.RUNNING)

            def save_checkpoint(agent_id: str, result: AgentExecutionResult) -> None:
                if agent_id == "reviewer":
                    self._checkpoints.save_reviewer(project_id, result)
                else:
                    self._checkpoints.save_specialist(project_id, agent_id, result)

            orchestration = await self._orchestrator.execute(
                project.prompt,
                planner.content,
                completed_results=checkpoint.specialists,
                review_result=checkpoint.reviewer,
                on_checkpoint=save_checkpoint,
            )
        except Exception:
            self._store.set_status(project_id, ProjectStatus.FAILED)
            raise

        self._store.set_status(project_id, ProjectStatus.COMPLETED)
        return ProjectExecutionResult(
            project_id=project_id,
            planner_output=planner.content,
            orchestration=orchestration,
        )

    def _require_project(self, project_id: UUID) -> Project:
        project = self._store.get(project_id)
        if project is None:
            raise KeyError(f"project not found: {project_id}")
        return project

    @staticmethod
    def _planner_task(project: Project) -> str:
        return (
            f"Project name: {project.name}\n\n"
            f"User request:\n{project.prompt}\n\n"
            "Create an implementation plan for the specialist agents. Identify required "
            "frontend, backend, database, security, testing, performance, integration, "
            "UI/UX, and sound work when applicable. Do not claim implementation has occurred."
        )
