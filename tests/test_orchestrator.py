import pytest

from src.orchestrator import OrchestrationError, Orchestrator, Task, TaskStatus


def test_dependencies_gate_tasks():
    planner = Task("plan", "planner", "Plan")
    frontend = Task("front", "frontend", "Build UI", dependencies=["plan"])
    orchestrator = Orchestrator([planner, frontend])
    assert [t.task_id for t in orchestrator.ready_tasks()] == ["plan"]
    orchestrator.mark_running("plan")
    orchestrator.mark_completed("plan")
    assert [t.task_id for t in orchestrator.ready_tasks()] == ["front"]


def test_cycle_is_rejected():
    with pytest.raises(OrchestrationError, match="cycle"):
        Orchestrator([
            Task("a", "planner", "A", dependencies=["b"]),
            Task("b", "architect", "B", dependencies=["a"]),
        ])


def test_unknown_dependency_is_rejected():
    with pytest.raises(OrchestrationError, match="unknown dependencies"):
        Orchestrator([Task("a", "planner", "A", dependencies=["missing"])])


def test_runner_failure_is_preserved():
    task = Task("backend", "backend", "Build API")
    orchestrator = Orchestrator([task])

    def fail(_task):
        raise RuntimeError("boom")

    assert orchestrator.run_ready(fail) == []
    assert task.status == TaskStatus.FAILED
    assert task.error == "boom"


def test_repair_limit_prevents_infinite_loop():
    task = Task("debug", "debugging", "Repair")
    orchestrator = Orchestrator([task], max_repair_cycles=1)
    orchestrator.mark_running("debug")
    orchestrator.mark_failed("debug", "first")
    orchestrator.request_repair("debug")
    orchestrator.mark_failed("debug", "again")
    # A repair attempt becomes attempt #2 only when scheduled by a future repair runner.
    task.attempts = 2
    with pytest.raises(OrchestrationError, match="Repair limit"):
        orchestrator.request_repair("debug")


def test_independent_tasks_are_ready_together():
    orchestrator = Orchestrator([
        Task("ui", "ui_ux", "Design"),
        Task("db", "database", "Schema"),
        Task("api", "backend", "API", dependencies=["db"]),
    ])
    assert {t.task_id for t in orchestrator.ready_tasks()} == {"ui", "db"}
