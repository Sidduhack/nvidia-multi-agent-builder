from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.task import TaskStatus


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=20_000)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    prompt: str
    status: str
    current_version: int = 0


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    agent: str
    objective: str
    dependencies: list[UUID]
    status: TaskStatus
    review_required: bool


class AgentStatusResponse(BaseModel):
    name: str
    description: str
    enabled: bool = True
    current_task_id: UUID | None = None
    status: str = "idle"


class ProjectEventResponse(BaseModel):
    project_id: UUID
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
