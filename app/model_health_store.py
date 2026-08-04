from __future__ import annotations

from typing import Protocol

from app.model_health import ModelHealth


class ModelHealthStore(Protocol):
    """Durable storage contract for learned model-health observations."""

    def load(self) -> tuple[ModelHealth, ...]:
        """Return all persisted model-health records."""
        ...

    def save(self, health: ModelHealth) -> None:
        """Insert or replace one model-health record."""
        ...
