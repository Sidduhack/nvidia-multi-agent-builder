from pydantic import BaseModel, Field

from app.models.registry import Capability


class AgentDefinition(BaseModel):
    name: str
    description: str
    system_prompt: str
    required_capabilities: set[Capability] = Field(default_factory=set)
    preferred_model: str | None = None
    allowed_paths: list[str] = Field(default_factory=list)
    max_retries: int = Field(default=2, ge=0, le=10)


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}

    def register(self, agent: AgentDefinition) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent already registered: {agent.name}")
        self._agents[agent.name] = agent

    def get(self, name: str) -> AgentDefinition:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {name}") from exc

    def all(self) -> list[AgentDefinition]:
        return list(self._agents.values())


def _definition(
    name: str,
    description: str,
    prompt: str,
    capabilities: set[Capability],
) -> AgentDefinition:
    return AgentDefinition(
        name=name,
        description=description,
        system_prompt=prompt,
        required_capabilities=capabilities,
    )


def default_agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    definitions = [
        _definition(
            "planner",
            "Extract requirements and produce an executable development plan.",
            "You are the Project Manager. Produce requirements and dependency-aware tasks. Do not generate application code.",
            {Capability.PLANNING, Capability.REASONING},
        ),
        _definition(
            "architect",
            "Define system boundaries, contracts, data architecture, and technical decisions.",
            "You are the System Architect. Define approved architecture and contracts. Never silently override requirements.",
            {Capability.REASONING, Capability.LONG_CONTEXT},
        ),
        _definition(
            "uiux",
            "Design information architecture, journeys, states, accessibility, and responsive behavior.",
            "You are the UI/UX Designer. Produce implementation-ready UX specifications, not decorative filler. Prioritize accessibility and clarity.",
            {Capability.REASONING},
        ),
        _definition(
            "frontend",
            "Implement accessible frontend code against approved UI and API contracts.",
            "You are the Frontend Engineer. Build modular accessible UI. Never invent backend endpoints; report contract conflicts instead.",
            {Capability.CODING, Capability.REASONING},
        ),
        _definition(
            "backend",
            "Implement server APIs, business logic, validation, auth, and integrations.",
            "You are the Backend Engineer. Follow approved API and security contracts. Keep secrets server-side and validate untrusted input.",
            {Capability.CODING, Capability.REASONING},
        ),
        _definition(
            "database",
            "Design schemas, constraints, indexes, migrations, policies, and recovery considerations.",
            "You are the Database Engineer. Design normalized, constrained, migration-friendly data structures and document access policies.",
            {Capability.REASONING, Capability.CODING},
        ),
        _definition(
            "security",
            "Review generated systems for application and agent-execution security risks.",
            "You are the Security Engineer. Review defensively for auth, injection, secret exposure, access control, unsafe execution, and dependency risks. Return actionable findings.",
            {Capability.SECURITY, Capability.REASONING},
        ),
        _definition(
            "reviewer",
            "Review code for correctness, maintainability, contracts, and architecture violations.",
            "You are the Code Reviewer. Prefer small actionable findings over unnecessary rewrites. Verify imports, paths, contracts, duplication, and correctness.",
            {Capability.CODING, Capability.REASONING},
        ),
        _definition(
            "testing",
            "Design unit, integration, and end-to-end tests for important user journeys.",
            "You are the Testing Engineer. Create meaningful tests from approved requirements and contracts. Never claim a test passed unless execution evidence says so.",
            {Capability.CODING, Capability.REASONING},
        ),
        _definition(
            "debugging",
            "Diagnose build and test failures and propose minimal reliable repairs.",
            "You are the Debugging Engineer. Read complete errors, find root causes, change only affected code, and require retesting after repairs.",
            {Capability.DEBUGGING, Capability.CODING, Capability.REASONING},
        ),
        _definition(
            "performance",
            "Identify meaningful frontend, API, database, caching, and resource improvements.",
            "You are the Performance Engineer. Optimize only where evidence indicates meaningful benefit; avoid speculative complexity.",
            {Capability.REASONING, Capability.CODING},
        ),
        _definition(
            "integrator",
            "Verify the complete generated project and resolve cross-agent integration conflicts.",
            "You are the Final Integration Engineer. Verify structure, dependencies, imports, contracts, configuration, and build readiness. Never hide unresolved failures.",
            {Capability.REASONING, Capability.CODING, Capability.LONG_CONTEXT},
        ),
    ]
    for definition in definitions:
        registry.register(definition)
    return registry
