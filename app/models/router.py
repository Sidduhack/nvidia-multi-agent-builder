from app.models.registry import Capability, ModelProfile, ModelRegistry


class NoCompatibleModelError(RuntimeError):
    pass


class ModelRouter:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def select(
        self,
        required: set[Capability],
        preferred_model: str | None = None,
    ) -> ModelProfile:
        if preferred_model:
            preferred = self.registry.get(preferred_model)
            if preferred and preferred.enabled and required.issubset(preferred.capabilities):
                return preferred

        candidates = self.registry.candidates(required)
        if not candidates:
            names = ", ".join(sorted(capability.value for capability in required))
            raise NoCompatibleModelError(f"No enabled model satisfies capabilities: {names}")
        return candidates[0]
