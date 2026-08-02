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


def default_agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        AgentDefinition(
            name="planner",
            description="Extract requirements and produce an executable development plan.",
            system_prompt=(
                "You are the Project Manager. Analyze the project request, separate functional and "
                "non-functional requirements, identify assumptions and unresolved decisions, and "
                "produce small dependency-aware tasks. Do not generate application code."
            ),
            required_capabilities={Capability.PLANNING, Capability.REASONING},
        )
    )
    registry.register(
        AgentDefinition(
            name="architect",
            description="Define system boundaries, contracts, data architecture, and technical decisions.",
            system_prompt=(
                "You are the System Architect. Work from approved requirements. Define architecture, "
                "folder boundaries, API contracts, database boundaries, security constraints, and "
                "scalability decisions. Do not silently override approved requirements."
            ),
            required_capabilities={Capability.REASONING, Capability.LONG_CONTEXT},
        )
    )
    return registry
