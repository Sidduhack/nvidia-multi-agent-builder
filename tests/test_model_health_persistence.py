from datetime import UTC, datetime

from app.model_health import ModelHealthRegistry, ModelHealthState
from app.sqlite_model_health_store import SQLiteModelHealthStore

NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)


def test_registry_restores_success_history_after_restart(tmp_path) -> None:
    path = tmp_path / "health.db"
    first = ModelHealthRegistry(store=SQLiteModelHealthStore(path))
    first.record_success("fast/model", 1.5, now=NOW)
    first.record_success("fast/model", 0.5, now=NOW)

    restarted = ModelHealthRegistry(store=SQLiteModelHealthStore(path))
    health = restarted.get("fast/model")

    assert health.success_count == 2
    assert health.average_latency_seconds == 1.0
    assert health.last_success == NOW


def test_registry_restores_failure_and_cooldown_after_restart(tmp_path) -> None:
    path = tmp_path / "health.db"
    first = ModelHealthRegistry(
        failure_threshold=1,
        cooldown_seconds=60,
        store=SQLiteModelHealthStore(path),
    )
    first.record_failure("bad/model", now=NOW)

    restarted = ModelHealthRegistry(
        failure_threshold=1,
        cooldown_seconds=60,
        store=SQLiteModelHealthStore(path),
    )

    assert restarted.get("bad/model").failure_count == 1
    assert restarted.get("bad/model").state(now=NOW) is ModelHealthState.COOLDOWN
    assert not restarted.available("bad/model", now=NOW)


def test_persisted_latency_changes_routing_after_restart(tmp_path) -> None:
    path = tmp_path / "health.db"
    first = ModelHealthRegistry(store=SQLiteModelHealthStore(path))
    first.record_success("slow/model", 10.0, now=NOW)
    first.record_success("fast/model", 1.0, now=NOW)

    restarted = ModelHealthRegistry(store=SQLiteModelHealthStore(path))

    assert restarted.order_candidates(
        ("slow/model", "fast/model"), now=NOW
    ) == ("fast/model", "slow/model")


def test_registry_without_store_remains_in_memory_only() -> None:
    registry = ModelHealthRegistry()
    registry.record_success("test/model", 2.0, now=NOW)

    fresh_registry = ModelHealthRegistry()

    assert registry.get("test/model").success_count == 1
    assert fresh_registry.get("test/model").success_count == 0
