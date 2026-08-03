from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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

    def set_status(self, project_id: UUID, project_status: ProjectStatus) -> Project:
        with self._lock:
            project = self._projects.get(project_id)
            if project is None:
                raise KeyError(f"project not found: {project_id}")
            updated = project.model_copy(
                update={"status": project_status, "updated_at": datetime.now(UTC)}
            )
            self._projects[project_id] = updated
            return updated


store = ProjectStore()
