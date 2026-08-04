from datetime import UTC, datetime, timedelta

from app.model_health import ModelHealth
from app.sqlite_model_health_store import SQLiteModelHealthStore


NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)


def test_empty_store_loads_no_health_records(tmp_path) -> None:
    store = SQLiteModelHealthStore(tmp_path / "health.db")

    assert store.load() == ()


def test_store_round_trips_complete_model_health(tmp_path) -> None:
    path = tmp_path / "health.db"
    store = SQLiteModelHealthStore(path)
    expected = ModelHealth(
        model="test/model",
        success_count=4,
        failure_count=2,
        consecutive_failures=2,
        average_latency_seconds=3.75,
        last_success=NOW - timedelta(minutes=5),
        last_failure=NOW,
        cooldown_until=NOW + timedelta(minutes=1),
    )

    store.save(expected)

    restarted_store = SQLiteModelHealthStore(path)
    assert restarted_store.load() == (expected,)


def test_save_replaces_existing_model_health(tmp_path) -> None:
    store = SQLiteModelHealthStore(tmp_path / "health.db")
    store.save(ModelHealth(model="test/model", success_count=1))

    updated = ModelHealth(
        model="test/model",
        success_count=2,
        average_latency_seconds=1.25,
        last_success=NOW,
    )
    store.save(updated)

    assert store.load() == (updated,)


def test_multiple_models_are_persisted_independently(tmp_path) -> None:
    store = SQLiteModelHealthStore(tmp_path / "health.db")
    first = ModelHealth(model="b/model", success_count=2)
    second = ModelHealth(model="a/model", failure_count=1, last_failure=NOW)

    store.save(first)
    store.save(second)

    assert store.load() == (second, first)
