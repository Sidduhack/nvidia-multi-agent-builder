"""Dependency-aware multi-agent task orchestrator.

Phase 9 establishes deterministic task state management and scheduling. Actual
agent execution is injected through a runner so orchestration stays independent
from model/provider implementations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    REVIEWING = "reviewing"
    TESTING = "testing"
    FAILED = "failed"
    REPAIRING = "repairing"
    COMPLETED = "completed"


@dataclass
class Task:
    task_id: str
    agent: str
    objective: str
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    files: list[str] = field(default_factory=list)
    review_required: bool = True
    attempts: int = 0
    error: str | None = None


class OrchestrationError(RuntimeError):
    pass


class Orchestrator:
    def __init__(self, tasks: Iterable[Task], *, max_repair_cycles: int = 3) -> None:
        task_list = list(tasks)
        self.tasks = {task.task_id: task for task in task_list}
        if len(self.tasks) != len(task_list):
            raise OrchestrationError("Duplicate task IDs are not allowed")
        if max_repair_cycles < 0:
            raise OrchestrationError("max_repair_cycles cannot be negative")
        self.max_repair_cycles = max_repair_cycles
        self._validate_graph()

    def _validate_graph(self) -> None:
        for task in self.tasks.values():
            missing = [d for d in task.dependencies if d not in self.tasks]
            if missing:
                raise OrchestrationError(
                    f"Task {task.task_id} has unknown dependencies: {', '.join(missing)}"
                )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise OrchestrationError("Task dependency graph contains a cycle")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in self.tasks[task_id].dependencies:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in self.tasks:
            visit(task_id)

    def ready_tasks(self) -> list[Task]:
        ready: list[Task] = []
        for task in self.tasks.values():
            if task.status not in {TaskStatus.PENDING, TaskStatus.WAITING}:
                continue
            dependency_states = [self.tasks[d].status for d in task.dependencies]
            if any(state == TaskStatus.FAILED for state in dependency_states):
                task.status = TaskStatus.WAITING
                continue
            if all(state == TaskStatus.COMPLETED for state in dependency_states):
                ready.append(task)
            else:
                task.status = TaskStatus.WAITING
        return ready

    def mark_running(self, task_id: str) -> Task:
        task = self._task(task_id)
        if task not in self.ready_tasks():
            raise OrchestrationError(f"Task {task_id} is not ready")
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        task.error = None
        return task

    def mark_completed(self, task_id: str) -> Task:
        task = self._task(task_id)
        if task.status not in {
            TaskStatus.RUNNING,
            TaskStatus.REVIEWING,
            TaskStatus.TESTING,
            TaskStatus.REPAIRING,
        }:
            raise OrchestrationError(f"Task {task_id} cannot complete from {task.status}")
        task.status = TaskStatus.COMPLETED
        task.error = None
        return task

    def mark_failed(self, task_id: str, error: str) -> Task:
        task = self._task(task_id)
        if task.status not in {
            TaskStatus.RUNNING,
            TaskStatus.REVIEWING,
            TaskStatus.TESTING,
            TaskStatus.REPAIRING,
        }:
            raise OrchestrationError(f"Task {task_id} cannot fail from {task.status}")
        task.status = TaskStatus.FAILED
        task.error = error
        return task

    def request_repair(self, task_id: str) -> Task:
        task = self._task(task_id)
        if task.status != TaskStatus.FAILED:
            raise OrchestrationError("Only failed tasks can enter repair")
        repairs_used = max(task.attempts - 1, 0)
        if repairs_used >= self.max_repair_cycles:
            raise OrchestrationError(f"Repair limit reached for task {task_id}")
        task.status = TaskStatus.REPAIRING
        return task

    def run_ready(self, runner: Callable[[Task], None]) -> list[str]:
        """Run one scheduling wave. Parallel execution can wrap this boundary later."""
        completed: list[str] = []
        for task in list(self.ready_tasks()):
            self.mark_running(task.task_id)
            try:
                runner(task)
            except Exception as exc:  # runner boundary normalizes failures into state
                self.mark_failed(task.task_id, str(exc))
            else:
                self.mark_completed(task.task_id)
                completed.append(task.task_id)
        return completed

    def _task(self, task_id: str) -> Task:
        try:
            return self.tasks[task_id]
        except KeyError as exc:
            raise OrchestrationError(f"Unknown task: {task_id}") from exc
