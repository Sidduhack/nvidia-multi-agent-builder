from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.model_health import ModelHealth


class SQLiteModelHealthStore:
    """SQLite persistence for learned model health and latency observations."""

    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS model_health (
                    model TEXT PRIMARY KEY,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    consecutive_failures INTEGER NOT NULL DEFAULT 0,
                    average_latency_seconds REAL,
                    last_success TEXT,
                    last_failure TEXT,
                    cooldown_until TEXT
                )
                """
            )

    def load(self) -> tuple[ModelHealth, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT model, success_count, failure_count, consecutive_failures,
                       average_latency_seconds, last_success, last_failure, cooldown_until
                FROM model_health
                ORDER BY model
                """
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, health: ModelHealth) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO model_health (
                    model, success_count, failure_count, consecutive_failures,
                    average_latency_seconds, last_success, last_failure, cooldown_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model) DO UPDATE SET
                    success_count = excluded.success_count,
                    failure_count = excluded.failure_count,
                    consecutive_failures = excluded.consecutive_failures,
                    average_latency_seconds = excluded.average_latency_seconds,
                    last_success = excluded.last_success,
                    last_failure = excluded.last_failure,
                    cooldown_until = excluded.cooldown_until
                """,
                (
                    health.model,
                    health.success_count,
                    health.failure_count,
                    health.consecutive_failures,
                    health.average_latency_seconds,
                    self._serialize_datetime(health.last_success),
                    self._serialize_datetime(health.last_failure),
                    self._serialize_datetime(health.cooldown_until),
                ),
            )

    @staticmethod
    def _serialize_datetime(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value is not None else None

    @classmethod
    def _from_row(cls, row: sqlite3.Row) -> ModelHealth:
        return ModelHealth(
            model=row["model"],
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            consecutive_failures=row["consecutive_failures"],
            average_latency_seconds=row["average_latency_seconds"],
            last_success=cls._parse_datetime(row["last_success"]),
            last_failure=cls._parse_datetime(row["last_failure"]),
            cooldown_until=cls._parse_datetime(row["cooldown_until"]),
        )
