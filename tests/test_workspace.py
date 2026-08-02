import pytest

from app.workspace import Workspace, WorkspaceError


def test_write_read_and_revision_control() -> None:
    workspace = Workspace()
    first = workspace.write(
        "frontend/src/App.tsx",
        "v1",
        agent="frontend",
        task_id="frontend-001",
        reason="Create application shell",
    )
    assert first.revision == 1

    second = workspace.write(
        "frontend/src/App.tsx",
        "v2",
        agent="frontend",
        task_id="frontend-001",
        reason="Add navigation",
        expected_revision=1,
    )
    assert second.revision == 2
    assert workspace.read("frontend/src/App.tsx").content == "v2"


def test_rejects_workspace_escape_paths() -> None:
    workspace = Workspace()
    for path in ("../secret", "/etc/passwd", "C:\\secret.txt"):
        with pytest.raises(WorkspaceError):
            workspace.write(path, "x", agent="agent", task_id="task", reason="test")


def test_lock_prevents_other_task_from_overwriting_file() -> None:
    workspace = Workspace()
    workspace.acquire("backend/api.py", "backend-001")

    with pytest.raises(WorkspaceError, match="locked"):
        workspace.write(
            "backend/api.py",
            "unsafe overwrite",
            agent="debugger",
            task_id="debug-001",
            reason="Attempt conflicting edit",
        )

    workspace.release("backend/api.py", "backend-001")
    record = workspace.write(
        "backend/api.py",
        "safe write",
        agent="debugger",
        task_id="debug-001",
        reason="Apply approved repair",
    )
    assert record.last_task_id == "debug-001"


def test_stale_revision_is_rejected() -> None:
    workspace = Workspace()
    workspace.write("README.md", "one", agent="planner", task_id="p1", reason="create")

    with pytest.raises(WorkspaceError, match="revision"):
        workspace.write(
            "README.md",
            "stale",
            agent="planner",
            task_id="p2",
            reason="stale edit",
            expected_revision=0,
        )


def test_delete_respects_lock_owner() -> None:
    workspace = Workspace()
    workspace.write("a.txt", "a", agent="agent", task_id="task-a", reason="create")
    workspace.acquire("a.txt", "task-a")

    with pytest.raises(WorkspaceError, match="locked"):
        workspace.delete("a.txt", task_id="task-b")

    workspace.delete("a.txt", task_id="task-a")
    with pytest.raises(WorkspaceError, match="not found"):
        workspace.read("a.txt")
