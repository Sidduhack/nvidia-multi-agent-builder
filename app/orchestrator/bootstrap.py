from uuid import UUID

from app.memory.project import ProjectMemory
from app.orchestrator.graph import TaskGraph
from app.schemas.task import AgentTask


def bootstrap_project(project_id: UUID, request: str, memory: ProjectMemory) -> TaskGraph:
    """Create the first dependency chain for a new project request."""
    memory.append(project_id, "requirements", {"raw_request": request})

    planner = AgentTask(
        project_id=project_id,
        agent="planner",
        objective="Analyze the project request and produce approved-ready requirements and a task plan.",
    )
    architect = AgentTask(
        project_id=project_id,
        agent="architect",
        objective="Create the system architecture and technical contracts from the project requirements.",
        dependencies=[planner.id],
    )

    graph = TaskGraph()
    graph.add(planner)
    graph.add(architect)
    return graph
