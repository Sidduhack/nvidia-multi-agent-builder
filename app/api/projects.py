from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.execution import AgentExecutionService
from app.performance import PerformanceController, PerformanceLimits
from app.project_execution import ProjectExecutionResult, ProjectExecutionService
from app.project_store import Project, ProjectCreate, ProjectStatus, ProjectSummary, store
from app.providers.nvidia import NvidiaProvider, NvidiaProviderError

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


class AgentOutput(BaseModel):
    agent_id: str
    model: str
    content: str


class ProjectStartResponse(BaseModel):
    project_id: UUID
    status: ProjectStatus
    planner_output: str
    specialists: list[AgentOutput]
    review: AgentOutput


@lru_cache
def get_project_execution_service() -> ProjectExecutionService:
    settings = get_settings()
    performance = PerformanceController(
        PerformanceLimits(max_parallel_agents=settings.max_parallel_agents)
    )
    provider = NvidiaProvider(settings)
    runner = AgentExecutionService(
        provider,
        default_model=settings.nvidia_default_model,
        performance=performance,
    )
    return ProjectExecutionService(
        store,
        runner,
        settings,
        max_parallel_agents=settings.max_parallel_agents,
    )


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate) -> Project:
    return store.create(payload)


@router.get("", response_model=list[ProjectSummary])
async def list_projects() -> list[Project]:
    return store.list()


@router.post("/{project_id}/start", response_model=ProjectStartResponse)
async def start_project(project_id: UUID) -> ProjectStartResponse:
    if store.get(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        result: ProjectExecutionResult = await get_project_execution_service().start(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except NvidiaProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    project = store.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return ProjectStartResponse(
        project_id=result.project_id,
        status=project.status,
        planner_output=result.planner_output,
        specialists=[
            AgentOutput(agent_id=item.agent_id, model=item.model, content=item.content)
            for item in result.orchestration.specialist_results
        ],
        review=AgentOutput(
            agent_id=result.orchestration.review.agent_id,
            model=result.orchestration.review.model,
            content=result.orchestration.review.content,
        ),
    )


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID) -> Project:
    project = store.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
