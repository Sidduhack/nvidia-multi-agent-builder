from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelRoute:
    primary: str
    fallbacks: tuple[str, ...] = ()

    @property
    def candidates(self) -> tuple[str, ...]:
        return (self.primary, *self.fallbacks)


NEMOTRON_ULTRA = "nvidia/nemotron-3-ultra-550b-a55b"
NEMOTRON_SUPER = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
MINIMAX_M3 = "minimaxai/minimax-m3"
DEEPSEEK_V4_PRO = "deepseek-ai/deepseek-v4-pro"
LLAMA_33_70B = "meta/llama-3.3-70b-instruct"
LLAMA_VISION_90B = "meta/llama-3.2-90b-vision-instruct"
LLAMA_VISION_11B = "meta/llama-3.2-11b-vision-instruct"


VERIFIED_MODEL_ROUTES: dict[str, ModelRoute] = {
    "planner": ModelRoute(NEMOTRON_ULTRA, (NEMOTRON_SUPER, MINIMAX_M3)),
    "architect": ModelRoute(NEMOTRON_SUPER, (NEMOTRON_ULTRA, LLAMA_33_70B)),
    "ui-ux": ModelRoute(LLAMA_VISION_11B, (LLAMA_VISION_90B, NEMOTRON_SUPER)),
    "frontend": ModelRoute(MINIMAX_M3, (DEEPSEEK_V4_PRO, NEMOTRON_SUPER)),
    "backend": ModelRoute(DEEPSEEK_V4_PRO, (MINIMAX_M3, NEMOTRON_SUPER)),
    "database": ModelRoute(NEMOTRON_SUPER, (MINIMAX_M3, NEMOTRON_ULTRA)),
    "sound-engineer": ModelRoute(NEMOTRON_SUPER, (MINIMAX_M3,)),
    "security": ModelRoute(NEMOTRON_ULTRA, (NEMOTRON_SUPER, DEEPSEEK_V4_PRO)),
    "testing": ModelRoute(NEMOTRON_SUPER, (MINIMAX_M3, DEEPSEEK_V4_PRO)),
    "performance": ModelRoute(NEMOTRON_SUPER, (MINIMAX_M3,)),
    "integration": ModelRoute(MINIMAX_M3, (NEMOTRON_SUPER, DEEPSEEK_V4_PRO)),
    "debugging": ModelRoute(DEEPSEEK_V4_PRO, (MINIMAX_M3, NEMOTRON_SUPER)),
    "reviewer": ModelRoute(LLAMA_33_70B, (NEMOTRON_ULTRA, NEMOTRON_SUPER)),
}


def route_for_agent(agent_id: str, *, default_model: str) -> ModelRoute:
    """Return the verified route for an agent, or a safe configured default."""
    return VERIFIED_MODEL_ROUTES.get(agent_id, ModelRoute(default_model))
