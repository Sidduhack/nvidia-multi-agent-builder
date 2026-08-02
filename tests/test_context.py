from uuid import uuid4

from app.memory.project import ProjectMemory
from app.orchestrator.context import ContextBuilder


def test_planner_does_not_receive_unrelated_architecture_context() -> None:
    project_id = uuid4()
    memory = ProjectMemory()
    memory.append(project_id, "requirements", "build a dashboard")
    memory.append(project_id, "architecture", "internal architecture detail")
    context = ContextBuilder(memory).build(project_id, "planner")
    assert "requirements" in context
    assert "architecture" not in context
