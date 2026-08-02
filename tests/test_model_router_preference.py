from app.models.registry import Capability, ModelProfile, ModelRegistry
from app.models.router import ModelRouter


def test_router_ignores_preferred_model_without_required_capabilities() -> None:
    registry = ModelRegistry()
    registry.register(ModelProfile(model_id="preferred", capabilities={Capability.CODING}, cost_class=1))
    registry.register(ModelProfile(model_id="compatible", capabilities={Capability.REASONING}, cost_class=2))
    selected = ModelRouter(registry).select({Capability.REASONING}, preferred_model="preferred")
    assert selected.model_id == "compatible"
