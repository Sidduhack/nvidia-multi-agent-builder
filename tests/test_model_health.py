from datetime import datetime, timedelta, timezone

import pytest

from app.model_health import ModelHealthRegistry, ModelHealthState


NOW = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)


def test_unknown_model_starts_healthy() -> None:
    registry = ModelHealthRegistry()
    health = registry.get("test/model")

    assert health.state(now=NOW) is ModelHealthState.HEALTHY
    assert health.success_count == 0
    assert health.failure_count == 0


def test_success_tracks_count_and_average_latency() -> None:
    registry = ModelHealthRegistry()

    registry.record_success("test/model", 2.0, now=NOW)
    health = registry.record_success("test/model", 4.0, now=NOW)

    assert health.success_count == 2
    assert health.average_latency_seconds == pytest.approx(3.0)
    assert health.consecutive_failures == 0


def test_single_failure_marks_model_degraded() -> None:
    registry = ModelHealthRegistry(failure_threshold=2)

    health = registry.record_failure("test/model", now=NOW)

    assert health.failure_count == 1
    assert health.consecutive_failures == 1
    assert health.state(now=NOW) is ModelHealthState.DEGRADED


def test_repeated_failures_put_model_in_cooldown() -> None:
    registry = ModelHealthRegistry(failure_threshold=2, cooldown_seconds=60)

    registry.record_failure("test/model", now=NOW)
    health = registry.record_failure("test/model", now=NOW)

    assert health.state(now=NOW) is ModelHealthState.COOLDOWN
    assert registry.available("test/model", now=NOW) is False
    assert health.cooldown_until == NOW + timedelta(seconds=60)


def test_model_leaves_cooldown_after_deadline() -> None:
    registry = ModelHealthRegistry(failure_threshold=1, cooldown_seconds=60)
    registry.record_failure("test/model", now=NOW)

    later = NOW + timedelta(seconds=61)

    assert registry.get("test/model").state(now=later) is ModelHealthState.DEGRADED
    assert registry.available("test/model", now=later) is True


def test_success_recovers_model_and_clears_cooldown() -> None:
    registry = ModelHealthRegistry(failure_threshold=1, cooldown_seconds=60)
    registry.record_failure("test/model", now=NOW)

    health = registry.record_success("test/model", 1.5, now=NOW + timedelta(seconds=5))

    assert health.state(now=NOW + timedelta(seconds=5)) is ModelHealthState.HEALTHY
    assert health.consecutive_failures == 0
    assert health.cooldown_until is None


def test_candidate_order_prefers_healthy_then_degraded_then_cooldown() -> None:
    registry = ModelHealthRegistry(failure_threshold=2, cooldown_seconds=60)
    registry.record_failure("degraded", now=NOW)
    registry.record_failure("cooldown", now=NOW)
    registry.record_failure("cooldown", now=NOW)

    ordered = registry.order_candidates(
        ("cooldown", "degraded", "healthy"),
        now=NOW,
    )

    assert ordered == ("healthy", "degraded", "cooldown")


def test_invalid_registry_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="failure_threshold"):
        ModelHealthRegistry(failure_threshold=0)
    with pytest.raises(ValueError, match="cooldown_seconds"):
        ModelHealthRegistry(cooldown_seconds=0)
