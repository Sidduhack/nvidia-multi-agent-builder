from uuid import UUID

from app.memory.project import ProjectMemory


ROLE_CONTEXT: dict[str, list[str]] = {
    "planner": ["requirements", "decisions"],
    "architect": ["requirements", "decisions", "constraints"],
}


class ContextBuilder:
    def __init__(self, memory: ProjectMemory) -> None:
        self.memory = memory

    def build(self, project_id: UUID, agent_name: str) -> dict:
        categories = ROLE_CONTEXT.get(agent_name, ["requirements", "decisions"])
        return self.memory.context(project_id, categories)
