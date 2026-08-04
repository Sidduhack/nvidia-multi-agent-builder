from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class ModelHealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    COOLDOWN = "cooldown"


@dataclass(frozen=True, slots=True)
class ModelHealth:
    model: str
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    average_latency_seconds: float | None = None
    last_success: datetime | None = None
    last_failure: datetime | None = None
    cooldown_until: datetime | None = None

    def state(self, *, now: datetime | None = None) -> ModelHealthState:
        current = now or datetime.now(UTC)
        if self.cooldown_until is not None and current < self.cooldown_until:
            return ModelHealthState.COOLDOWN
        if self.consecutive_failures > 0:
            return ModelHealthState.DEGRADED
        return ModelHealthState.HEALTHY


class ModelHealthRegistry:
    """In-memory runtime health and latency history for model routing decisions."""

    def __init__(
        self,
        *,
        failure_threshold: int = 2,
        cooldown_seconds: float = 60.0,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be positive")
        if cooldown_seconds <= 0:
            raise ValueError("cooldown_seconds must be positive")
        self._failure_threshold = failure_threshold
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._models: dict[str, ModelHealth] = {}

    def get(self, model: str) -> ModelHealth:
        return self._models.get(model, ModelHealth(model=model))

    def record_success(
        self,
        model: str,
        latency_seconds: float,
        *,
        now: datetime | None = None,
    ) -> ModelHealth:
        if latency_seconds < 0:
            raise ValueError("latency_seconds must not be negative")
        current = now or datetime.now(UTC)
        previous = self.get(model)
        successes = previous.success_count + 1
        if previous.average_latency_seconds is None:
            average = latency_seconds
        else:
            average = (
                previous.average_latency_seconds * previous.success_count + latency_seconds
            ) / successes
        updated = replace(
            previous,
            success_count=successes,
            consecutive_failures=0,
            average_latency_seconds=average,
            last_success=current,
            cooldown_until=None,
        )
        self._models[model] = updated
        return updated

    def record_failure(
        self,
        model: str,
        *,
        now: datetime | None = None,
    ) -> ModelHealth:
        current = now or datetime.now(UTC)
        previous = self.get(model)
        consecutive = previous.consecutive_failures + 1
        cooldown_until = previous.cooldown_until
        if consecutive >= self._failure_threshold:
            cooldown_until = current + self._cooldown
        updated = replace(
            previous,
            failure_count=previous.failure_count + 1,
            consecutive_failures=consecutive,
            last_failure=current,
            cooldown_until=cooldown_until,
        )
        self._models[model] = updated
        return updated

    def available(self, model: str, *, now: datetime | None = None) -> bool:
        return self.get(model).state(now=now) is not ModelHealthState.COOLDOWN

    def order_candidates(
        self,
        candidates: tuple[str, ...],
        *,
        now: datetime | None = None,
    ) -> tuple[str, ...]:
        """Prefer healthy then degraded models and skip active cooldowns when possible.

        If every candidate is cooling down, return the original candidate chain as an
        emergency safety net so routing never produces an empty execution plan.
        """
        indexed = list(enumerate(candidates))
        active = [
            item
            for item in indexed
            if self.get(item[1]).state(now=now) is not ModelHealthState.COOLDOWN
        ]
        if not active:
            return candidates

        rank = {
            ModelHealthState.HEALTHY: 0,
            ModelHealthState.DEGRADED: 1,
            ModelHealthState.COOLDOWN: 2,
        }
        active.sort(key=lambda item: (rank[self.get(item[1]).state(now=now)], item[0]))
        return tuple(model for _, model in active)

    def snapshot(self) -> tuple[ModelHealth, ...]:
        return tuple(self._models.values())
