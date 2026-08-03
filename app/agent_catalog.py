from __future__ import annotations

from dataclasses import dataclass

from app.sound_engineer import SOUND_ENGINEER


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    agent_id: str
    display_name: str
    purpose: str


_AGENT_DEFINITIONS = (
    AgentDefinition("planner", "Planner", "Turn product requests into scoped requirements and tasks."),
    AgentDefinition("architect", "Architect", "Define system architecture, interfaces, and technical constraints."),
    AgentDefinition("ui-ux", "UI/UX Designer", "Design accessible, usable interfaces and interaction behavior."),
    AgentDefinition("frontend", "Frontend Engineer", "Implement client-side application code and interfaces."),
    AgentDefinition("backend", "Backend Engineer", "Implement APIs, services, and server-side application logic."),
    AgentDefinition("database", "Database Engineer", "Design persistence, schemas, migrations, and data access."),
    AgentDefinition("security", "Security Engineer", "Review generated changes and enforce security boundaries."),
    AgentDefinition("reviewer", "Code Reviewer", "Review correctness, maintainability, and integration quality."),
    AgentDefinition("testing", "Test Engineer", "Design and execute verification for generated projects."),
    AgentDefinition("debugging", "Debugging Engineer", "Diagnose failures and produce bounded repair changes."),
    AgentDefinition("performance", "Performance Engineer", "Measure and improve runtime and asset efficiency."),
    AgentDefinition("integration", "Integration Engineer", "Combine specialist output and verify system compatibility."),
    AgentDefinition(SOUND_ENGINEER.agent_id, SOUND_ENGINEER.display_name, SOUND_ENGINEER.purpose),
)

AGENT_CATALOG = {definition.agent_id: definition for definition in _AGENT_DEFINITIONS}

if len(AGENT_CATALOG) != len(_AGENT_DEFINITIONS):
    raise RuntimeError("agent catalog contains duplicate agent IDs")


def get_agent(agent_id: str) -> AgentDefinition:
    """Return a registered specialist or fail explicitly for unknown IDs."""
    try:
        return AGENT_CATALOG[agent_id]
    except KeyError as exc:
        raise KeyError(f"unknown agent: {agent_id}") from exc


def list_agents() -> tuple[AgentDefinition, ...]:
    """Return the stable canonical specialist set."""
    return _AGENT_DEFINITIONS
