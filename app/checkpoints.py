from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID

from app.execution import AgentExecutionResult


@dataclass(slots=True)
class ProjectCheckpoint:
    """Successful AI outputs retained so a failed project can resume without repeating work."""

    planner: AgentExecutionResult | None = None
    specialists: dict[str, AgentExecutionResult] = field(default_factory=dict)
    reviewer: AgentExecutionResult | None = None


class CheckpointStore:
    """Process-local checkpoint store; persistence can replace this behind the same API later."""

    def __init__(self) -> None:
        self._items: dict[UUID, ProjectCheckpoint] = {}
        self._lock = Lock()

    def get(self, project_id: UUID) -> ProjectCheckpoint:
        with self._lock:
            checkpoint = self._items.get(project_id)
            if checkpoint is None:
                checkpoint = ProjectCheckpoint()
                self._items[project_id] = checkpoint
            return ProjectCheckpoint(
                planner=checkpoint.planner,
                specialists=dict(checkpoint.specialists),
                reviewer=checkpoint.reviewer,
            )

    def save_planner(self, project_id: UUID, result: AgentExecutionResult) -> None:
        with self._lock:
            checkpoint = self._items.setdefault(project_id, ProjectCheckpoint())
            checkpoint.planner = result

    def save_specialist(
        self,
        project_id: UUID,
        agent_id: str,
        result: AgentExecutionResult,
    ) -> None:
        with self._lock:
            checkpoint = self._items.setdefault(project_id, ProjectCheckpoint())
            checkpoint.specialists[agent_id] = result

    def save_reviewer(self, project_id: UUID, result: AgentExecutionResult) -> None:
        with self._lock:
            checkpoint = self._items.setdefault(project_id, ProjectCheckpoint())
            checkpoint.reviewer = result

    def clear(self, project_id: UUID) -> None:
        with self._lock:
            self._items.pop(project_id, None)


checkpoint_store = CheckpointStore()
