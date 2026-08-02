from uuid import uuid4

from app.memory.project import ProjectMemory


def test_memory_get_returns_a_list_copy() -> None:
    project_id = uuid4()
    memory = ProjectMemory()
    memory.append(project_id, "requirements", "original")
    returned = memory.get(project_id, "requirements")
    returned.append("local mutation")
    assert memory.get(project_id, "requirements") == ["original"]
