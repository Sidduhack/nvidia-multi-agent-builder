from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING = "waiting"
    REVIEWING = "reviewing"
    TESTING = "testing"
    FAILED = "failed"
    REPAIRING = "repairing"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class AgentTask(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    agent: str
    objective: str = Field(min_length=1, max_length=4000)
    dependencies: list[UUID] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    allowed_paths: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    review_required: bool = True
    attempt: int = Field(default=0, ge=0)


class TaskResult(BaseModel):
    task_id: UUID
    status: TaskStatus
    summary: str
    warnings: list[str] = Field(default_factory=list)
    issues: list[dict[str, Any]] = Field(default_factory=list)
