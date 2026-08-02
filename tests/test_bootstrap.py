from uuid import uuid4

from app.memory.project import ProjectMemory
from app.orchestrator.bootstrap import bootstrap_project


def test_bootstrap_starts_with_planner_then_architect() -> None:
    project_id = uuid4()
    memory = ProjectMemory()
    graph = bootstrap_project(project_id, "Build a gaming website", memory)
    ready = graph.ready()
    assert len(ready) == 1
    assert ready[0].agent == "planner"
    architect = next(task for task in graph.tasks.values() if task.agent == "architect")
    assert architect.dependencies == [ready[0].id]
    assert memory.get(project_id, "requirements") == [{"raw_request": "Build a gaming website"}]
