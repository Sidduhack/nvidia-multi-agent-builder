from uuid import uuid4

import pytest

from app.orchestrator.graph import TaskGraph, TaskGraphError
from app.schemas.task import AgentTask


def test_graph_rejects_cycle_when_dependency_becomes_known() -> None:
    project_id = uuid4()
    first = AgentTask(project_id=project_id, agent="a", objective="a")
    second = AgentTask(project_id=project_id, agent="b", objective="b", dependencies=[first.id])
    first.dependencies = [second.id]
    graph = TaskGraph()
    graph.add(first)
    with pytest.raises(TaskGraphError):
        graph.add(second)
