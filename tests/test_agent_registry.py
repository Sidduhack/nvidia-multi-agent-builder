import pytest

from app.agents.definitions import AgentDefinition, AgentRegistry


def test_agent_registry_rejects_duplicate_names() -> None:
    registry = AgentRegistry()
    definition = AgentDefinition(name="planner", description="p", system_prompt="p")
    registry.register(definition)
    with pytest.raises(ValueError):
        registry.register(definition)
