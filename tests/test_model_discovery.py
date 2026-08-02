import pytest

from app.models.discovery import ModelDiscovery
from app.models.registry import Capability, ModelProfile, ModelRegistry
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse


class DiscoveryProvider(AIProvider):
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError

    async def stream(self, request: CompletionRequest):
        if False:
            yield ""

    async def list_models(self) -> list[str]:
        return ["configured", "new"]


@pytest.mark.asyncio
async def test_discovery_preserves_admin_configured_capabilities() -> None:
    registry = ModelRegistry()
    registry.register(ModelProfile(model_id="configured", capabilities={Capability.CODING}, enabled=True))
    profiles = await ModelDiscovery(DiscoveryProvider(), registry).refresh()
    configured = next(profile for profile in profiles if profile.model_id == "configured")
    new = next(profile for profile in profiles if profile.model_id == "new")
    assert configured.capabilities == {Capability.CODING}
    assert configured.enabled is True
    assert new.enabled is False
