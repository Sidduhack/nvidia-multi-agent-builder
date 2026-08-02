"""Capability/role based model routing for configurable NVIDIA models."""

from __future__ import annotations

import os
from dataclasses import dataclass


ROLE_ENV = {
    "planner": "NVIDIA_MODEL_PLANNER",
    "architect": "NVIDIA_MODEL_ARCHITECT",
    "ui_ux": "NVIDIA_MODEL_UI_UX",
    "frontend": "NVIDIA_MODEL_FRONTEND",
    "backend": "NVIDIA_MODEL_BACKEND",
    "database": "NVIDIA_MODEL_DATABASE",
    "security": "NVIDIA_MODEL_SECURITY",
    "reviewer": "NVIDIA_MODEL_REVIEWER",
    "testing": "NVIDIA_MODEL_TESTING",
    "debugging": "NVIDIA_MODEL_DEBUGGING",
    "performance": "NVIDIA_MODEL_PERFORMANCE",
    "integration": "NVIDIA_MODEL_INTEGRATION",
}


class ModelRoutingError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    source: str


def route_model(role: str) -> ModelRoute:
    """Resolve a role-specific model with an optional deployment default."""
    normalized = role.strip().lower().replace("-", "_").replace("/", "_")
    env_name = ROLE_ENV.get(normalized)
    if env_name is None:
        raise ModelRoutingError(f"Unknown agent role: {role}")

    role_model = os.getenv(env_name, "").strip()
    if role_model:
        return ModelRoute(provider="nvidia", model=role_model, source=env_name)

    default_model = os.getenv("NVIDIA_MODEL_DEFAULT", "").strip()
    if default_model:
        return ModelRoute(
            provider="nvidia", model=default_model, source="NVIDIA_MODEL_DEFAULT"
        )

    raise ModelRoutingError(
        f"No NVIDIA model configured for {normalized}; set {env_name} or NVIDIA_MODEL_DEFAULT"
    )
