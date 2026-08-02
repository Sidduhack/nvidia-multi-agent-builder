from enum import StrEnum

from pydantic import BaseModel, Field


class Capability(StrEnum):
    PLANNING = "planning"
    REASONING = "reasoning"
    CODING = "coding"
    DEBUGGING = "debugging"
    SECURITY = "security"
    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    LONG_CONTEXT = "long_context"
    EMBEDDING = "embedding"


class ModelProfile(BaseModel):
    provider: str = "nvidia"
    model_id: str
    capabilities: set[Capability] = Field(default_factory=set)
    context_limit: int | None = None
    output_limit: int | None = None
    latency_class: int = Field(default=3, ge=1, le=5)
    cost_class: int = Field(default=1, ge=1, le=5)
    enabled: bool = True


class ModelRegistry:
    """Runtime registry. Model IDs are configuration/data, never agent constants."""

    def __init__(self) -> None:
        self._models: dict[str, ModelProfile] = {}

    def register(self, profile: ModelProfile) -> None:
        self._models[profile.model_id] = profile

    def get(self, model_id: str) -> ModelProfile | None:
        return self._models.get(model_id)

    def candidates(self, required: set[Capability]) -> list[ModelProfile]:
        matches = [
            model
            for model in self._models.values()
            if model.enabled and required.issubset(model.capabilities)
        ]
        return sorted(matches, key=lambda model: (model.cost_class, model.latency_class))
