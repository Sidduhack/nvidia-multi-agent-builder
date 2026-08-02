from uuid import UUID

from app.schemas.task import AgentTask, TaskStatus


class TaskGraphError(ValueError):
    pass


class TaskGraph:
    def __init__(self) -> None:
        self.tasks: dict[UUID, AgentTask] = {}

    def add(self, task: AgentTask) -> None:
        if task.id in self.tasks:
            raise TaskGraphError(f"Duplicate task: {task.id}")
        if task.id in task.dependencies:
            raise TaskGraphError("A task cannot depend on itself")
        self.tasks[task.id] = task
        if self._has_cycle():
            del self.tasks[task.id]
            raise TaskGraphError("Task dependency graph cannot contain cycles")

    def ready(self) -> list[AgentTask]:
        completed = {
            task_id
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        }
        return [
            task
            for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and set(task.dependencies).issubset(completed)
        ]

    def _has_cycle(self) -> bool:
        visiting: set[UUID] = set()
        visited: set[UUID] = set()

        def visit(task_id: UUID) -> bool:
            if task_id in visiting:
                return True
            if task_id in visited or task_id not in self.tasks:
                return False
            visiting.add(task_id)
            for dependency in self.tasks[task_id].dependencies:
                if visit(dependency):
                    return True
            visiting.remove(task_id)
            visited.add(task_id)
            return False

        return any(visit(task_id) for task_id in self.tasks)
