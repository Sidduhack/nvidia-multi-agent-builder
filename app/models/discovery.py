from app.models.registry import ModelProfile, ModelRegistry
from app.providers.base import AIProvider


class ModelDiscovery:
    """Discover provider model IDs without inventing capabilities.

    Capability metadata is intentionally assigned by configuration/admin review because
    availability of a model does not prove support for a particular capability.
    """

    def __init__(self, provider: AIProvider, registry: ModelRegistry) -> None:
        self.provider = provider
        self.registry = registry

    async def refresh(self) -> list[ModelProfile]:
        discovered: list[ModelProfile] = []
        for model_id in await self.provider.list_models():
            existing = self.registry.get(model_id)
            if existing:
                discovered.append(existing)
                continue
            profile = ModelProfile(model_id=model_id, capabilities=set(), enabled=False)
            self.registry.register(profile)
            discovered.append(profile)
        return discovered
