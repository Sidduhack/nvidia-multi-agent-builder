from uuid import UUID

from app.memory.project import ProjectMemory

ROLE_CONTEXT: dict[str, list[str]] = {
    "planner": ["requirements", "decisions"],
    "architect": ["requirements", "decisions", "constraints"],
    "uiux": ["requirements", "architecture", "design_system", "decisions"],
    "frontend": ["requirements", "architecture", "api_contracts", "design_system", "decisions"],
    "backend": ["requirements", "architecture", "api_contracts", "database_schema", "decisions"],
    "database": ["requirements", "architecture", "data_requirements", "decisions"],
    "security": ["requirements", "architecture", "api_contracts", "database_schema", "security_findings", "decisions"],
    "reviewer": ["requirements", "architecture", "api_contracts", "review_targets", "decisions"],
    "testing": ["requirements", "architecture", "api_contracts", "test_targets", "decisions"],
    "debugging": ["architecture", "errors", "test_results", "debug_targets", "decisions"],
    "performance": ["architecture", "performance_evidence", "review_targets", "decisions"],
    "integrator": ["requirements", "architecture", "api_contracts", "database_schema", "test_results", "security_findings", "integration_state", "decisions"],
}


class ContextBuilder:
    def __init__(self, memory: ProjectMemory) -> None:
        self.memory = memory

    def build(self, project_id: UUID, agent_name: str) -> dict:
        categories = ROLE_CONTEXT.get(agent_name, ["requirements", "decisions"])
        return self.memory.context(project_id, categories)
