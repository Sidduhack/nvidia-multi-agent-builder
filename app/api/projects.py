from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


class ProjectStatus(StrEnum):
    CREATED = "created"
    PLANNING = "planning"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    prompt: str = Field(min_length=20, max_length=20_000)


class Project(BaseModel):
    id: UUID
    name: str
    prompt: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectStore:
    """Small process-local store until the persistence phase wires the approved DB schema."""

    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}
        self._lock = Lock()

    def create(self, payload: ProjectCreate) -> Project:
        now = datetime.now(UTC)
        project = Project(
            id=uuid4(),
            name=payload.name.strip(),
            prompt=payload.prompt.strip(),
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._projects[project.id] = project
        return project

    def get(self, project_id: UUID) -> Project | None:
        with self._lock:
            return self._projects.get(project_id)

    def list(self) -> list[Project]:
        with self._lock:
            return sorted(self._projects.values(), key=lambda item: item.created_at, reverse=True)


store = ProjectStore()


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate) -> Project:
    return store.create(payload)


@router.get("", response_model=list[ProjectSummary])
async def list_projects() -> list[Project]:
    return store.list()


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID) -> Project:
    project = store.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
