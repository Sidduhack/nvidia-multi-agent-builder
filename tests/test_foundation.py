from uuid import uuid4

import pytest

from app.models.registry import Capability, ModelProfile, ModelRegistry
from app.models.router import ModelRouter, NoCompatibleModelError
from app.orchestrator.graph import TaskGraph, TaskGraphError
from app.schemas.task import AgentTask, TaskStatus


def test_router_prefers_cheaper_compatible_model() -> None:
    registry = ModelRegistry()
    registry.register(
        ModelProfile(
            model_id="large-model",
            capabilities={Capability.CODING},
            cost_class=4,
        )
    )
    registry.register(
        ModelProfile(
            model_id="free-first-model",
            capabilities={Capability.CODING},
            cost_class=1,
        )
    )
    selected = ModelRouter(registry).select({Capability.CODING})
    assert selected.model_id == "free-first-model"


def test_router_fails_when_capability_is_missing() -> None:
    with pytest.raises(NoCompatibleModelError):
        ModelRouter(ModelRegistry()).select({Capability.SECURITY})


def test_task_graph_releases_dependency_after_completion() -> None:
    project_id = uuid4()
    first = AgentTask(project_id=project_id, agent="planner", objective="Plan")
    second = AgentTask(
        project_id=project_id,
        agent="architect",
        objective="Architect",
        dependencies=[first.id],
    )
    graph = TaskGraph()
    graph.add(first)
    graph.add(second)
    assert [task.id for task in graph.ready()] == [first.id]
    first.status = TaskStatus.COMPLETED
    assert [task.id for task in graph.ready()] == [second.id]


def test_task_cannot_depend_on_itself() -> None:
    task = AgentTask(project_id=uuid4(), agent="planner", objective="Plan")
    task.dependencies.append(task.id)
    with pytest.raises(TaskGraphError):
        TaskGraph().add(task)
