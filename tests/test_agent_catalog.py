from app.agent_catalog import AGENT_CATALOG, get_agent, list_agents

import pytest


EXPECTED_AGENT_IDS = {
    "planner",
    "architect",
    "ui-ux",
    "frontend",
    "backend",
    "database",
    "security",
    "reviewer",
    "testing",
    "debugging",
    "performance",
    "integration",
    "sound-engineer",
}


def test_catalog_contains_exactly_thirteen_specialists() -> None:
    assert set(AGENT_CATALOG) == EXPECTED_AGENT_IDS
    assert len(list_agents()) == 13


def test_sound_engineer_is_registered() -> None:
    sound = get_agent("sound-engineer")
    assert sound.display_name == "Sound Engineer"
    assert "audio" in sound.purpose.lower()


def test_unknown_agent_fails_explicitly() -> None:
    with pytest.raises(KeyError, match="unknown agent"):
        get_agent("imaginary-agent")
