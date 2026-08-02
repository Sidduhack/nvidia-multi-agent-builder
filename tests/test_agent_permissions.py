from app.agents.definitions import default_agent_registry


def test_planner_and_architect_do_not_have_file_write_permissions_yet() -> None:
    registry = default_agent_registry()
    assert registry.get("planner").allowed_paths == []
    assert registry.get("architect").allowed_paths == []
