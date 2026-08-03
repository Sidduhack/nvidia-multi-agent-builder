from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.execution import AgentExecutionResult
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


class ProjectExecutionService:
    """Own project state transitions while delegating AI work to the agent runtime."""

    def __init__(
        self,
        store: ProjectStore,
        runner: AgentRunner,
        model_resolver: ModelResolver,
    ) -> None:
        self._store = store
        self._runner = runner
        self._model_resolver = model_resolver

    async def start(self, project_id: UUID) -> ProjectExecutionResult:
        project = self._require_project(project_id)
        if project.status is not ProjectStatus.CREATED:
            raise ValueError(f"project cannot start from status {project.status}")

        self._store.set_status(project_id, ProjectStatus.PLANNING)
        try:
            planner = await self._runner.execute(
                "planner",
                self._planner_task(project),
                model=self._model_resolver.model_for_agent("planner"),
            )
        except Exception:
            self._store.set_status(project_id, ProjectStatus.FAILED)
            raise

        self._store.set_status(project_id, ProjectStatus.RUNNING)
        return ProjectExecutionResult(project_id=project_id, planner_output=planner.content)

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
