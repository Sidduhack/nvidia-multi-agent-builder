from uuid import uuid4

from app.orchestrator.graph import TaskGraph
from app.schemas.task import AgentTask


def test_independent_tasks_are_ready_together() -> None:
    project_id = uuid4()
    graph = TaskGraph()
    first = AgentTask(project_id=project_id, agent="frontend", objective="frontend")
    second = AgentTask(project_id=project_id, agent="backend", objective="backend")
    graph.add(first)
    graph.add(second)
    assert {task.id for task in graph.ready()} == {first.id, second.id}
