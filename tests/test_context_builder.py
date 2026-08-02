from uuid import uuid4

from app.memory.project import ProjectMemory
from app.orchestrator.context import ContextBuilder


def test_architect_receives_requirements_constraints_and_decisions() -> None:
    project_id = uuid4()
    memory = ProjectMemory()
    memory.append(project_id, "requirements", "req")
    memory.append(project_id, "constraints", "free-first")
    memory.append(project_id, "decisions", "decision")
    memory.append(project_id, "private-debug-log", "not relevant")
    context = ContextBuilder(memory).build(project_id, "architect")
    assert set(context) == {"requirements", "constraints", "decisions"}
