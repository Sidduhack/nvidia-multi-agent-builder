from uuid import uuid4

from app.agents.definitions import default_agent_registry
from app.memory.project import ProjectMemory
from app.orchestrator.context import ContextBuilder


EXPECTED_AGENTS = {
    "planner",
    "architect",
    "uiux",
    "frontend",
    "backend",
    "database",
    "security",
    "reviewer",
    "testing",
    "debugging",
    "performance",
    "integrator",
}


def test_default_registry_contains_full_specialized_team() -> None:
    registry = default_agent_registry()
    assert {agent.name for agent in registry.all()} == EXPECTED_AGENTS


def test_specialized_agents_have_distinct_prompts() -> None:
    prompts = [agent.system_prompt for agent in default_agent_registry().all()]
    assert len(prompts) == len(set(prompts))


def test_frontend_context_contains_contract_but_not_database_schema() -> None:
    project_id = uuid4()
    memory = ProjectMemory()
    memory.append(project_id, "api_contracts", "GET /projects")
    memory.append(project_id, "database_schema", "private database detail")
    context = ContextBuilder(memory).build(project_id, "frontend")
    assert context["api_contracts"] == ["GET /projects"]
    assert "database_schema" not in context


def test_debugger_receives_errors_but_not_unrelated_requirements() -> None:
    project_id = uuid4()
    memory = ProjectMemory()
    memory.append(project_id, "errors", "build failed")
    memory.append(project_id, "requirements", "unrelated raw request")
    context = ContextBuilder(memory).build(project_id, "debugging")
    assert context["errors"] == ["build failed"]
    assert "requirements" not in context
