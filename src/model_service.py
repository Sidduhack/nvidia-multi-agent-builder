"""Single orchestration entry point for role-routed NVIDIA model calls."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .model_router import ModelRoute, route_model
from .providers.nvidia import NVIDIAProvider


class ModelService:
    def __init__(self, provider: NVIDIAProvider | None = None) -> None:
        self.provider = provider

    def complete(
        self,
        *,
        role: str,
        messages: Sequence[Mapping[str, Any]],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> tuple[str, ModelRoute]:
        route = route_model(role)
        provider = self.provider or NVIDIAProvider()
        response = provider.chat_completion(
            model=route.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return provider.assistant_text(response), route
